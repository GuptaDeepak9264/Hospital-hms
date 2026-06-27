"""
Appointment booking service.

═══════════════════════════════════════════════════════════════
RACE CONDITION HANDLING — Design Decision
═══════════════════════════════════════════════════════════════

OPTION 1 — Simple query (WRONG approach):
    slot = DoctorAvailability.objects.get(pk=availability_id)
    if slot.is_booked:
        raise ValidationError("Slot already booked.")
    slot.is_booked = True
    slot.save()
    Appointment.objects.create(...)

  Problem: Two concurrent requests can both read is_booked=False,
  both pass the check, and both create an Appointment → double booking.
  This is a classic TOCTOU (time-of-check / time-of-use) bug.

OPTION 2 — transaction.atomic() + select_for_update() (CORRECT approach):
    with transaction.atomic():
        slot = DoctorAvailability.objects.select_for_update().get(pk=id)
        if slot.is_booked:
            raise ValidationError(...)
        slot.is_booked = True
        slot.save()
        Appointment.objects.create(...)

  How it works:
  • transaction.atomic() opens a DB transaction.
  • select_for_update() issues a SELECT … FOR UPDATE SQL statement.
    The database acquires a row-level exclusive lock on that row.
  • Any concurrent request hitting the same row blocks (waits) until
    the first transaction commits or rolls back.
  • After the lock is released, the second request re-reads the row
    and sees is_booked=True → correctly returns a 409 Conflict.

  We chose Option 2. It guarantees exactly-once booking even under
  high concurrency without application-level mutexes or queues.
═══════════════════════════════════════════════════════════════
"""

import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from appointments.models import Appointment
from availability.models import DoctorAvailability
from calendar_service.services import CalendarService
from email_client.client import EmailServiceClient
from patients.models import Patient

logger = logging.getLogger(__name__)


class AppointmentService:
    """Business logic for creating and managing appointments."""

    @staticmethod
    @transaction.atomic
    def book_slot(patient: Patient, availability_id: int, notes: str = "") -> Appointment:
        """
        Atomically book a DoctorAvailability slot for a patient.

        Steps:
          1. Lock the row with SELECT FOR UPDATE (blocks concurrent requests).
          2. Validate the slot is still available and in the future.
          3. Mark slot as booked.
          4. Create the Appointment record.
          5. (Outside atomic) Trigger calendar events and confirmation email.
        """
        # ── Step 1: acquire row-level lock ────────────────────────────────────
        try:
            slot = (
                DoctorAvailability.objects.select_for_update()
                .select_related("doctor__user")
                .get(pk=availability_id)
            )
        except DoctorAvailability.DoesNotExist:
            raise ValidationError("Availability slot not found.")

        # ── Step 2: business-rule checks ─────────────────────────────────────
        if slot.is_booked:
            raise ValidationError(
                "This slot has already been booked by another patient. Please choose a different slot."
            )

        if slot.start_time <= timezone.now():
            raise ValidationError("Cannot book a slot that is in the past.")

        # Prevent patient from double-booking same doctor on same day
        existing = Appointment.objects.filter(
            patient=patient,
            availability__doctor=slot.doctor,
            availability__start_time__date=slot.start_time.date(),
            status="confirmed",
        ).exists()
        if existing:
            raise ValidationError(
                "You already have a confirmed appointment with this doctor on that day."
            )

        # ── Step 3: mark slot as booked ───────────────────────────────────────
        slot.is_booked = True
        slot.save(update_fields=["is_booked", "updated_at"])

        # ── Step 4: create appointment record ─────────────────────────────────
        appointment = Appointment.objects.create(
            patient=patient,
            availability=slot,
            notes=notes,
            status="confirmed",
        )

        logger.info(
            "Appointment #%s booked: patient=%s, doctor=%s, slot=%s",
            appointment.pk,
            patient.user.email,
            slot.doctor.user.email,
            slot.start_time,
        )

        # ── Step 5: post-booking side-effects (outside the critical path) ─────
        # These are fire-and-forget; failures do NOT roll back the booking.
        AppointmentService._post_booking_tasks(appointment)

        return appointment

    @staticmethod
    def _post_booking_tasks(appointment: Appointment) -> None:
        """
        Trigger Google Calendar events and send confirmation email.
        Called after the atomic transaction commits.
        Failures are logged but do NOT affect the booking.
        """
        # Google Calendar events
        try:
            CalendarService.create_booking_events(appointment)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Calendar event creation failed for appointment #%s: %s",
                appointment.pk,
                exc,
            )

        # Confirmation email via serverless email service
        try:
            EmailServiceClient.send_booking_confirmation(
                recipient_email=appointment.patient.user.email,
                recipient_name=appointment.patient.user.get_full_name(),
                doctor_name=appointment.availability.doctor.user.get_full_name(),
                appointment_datetime=appointment.availability.start_time.strftime(
                    "%Y-%m-%d %H:%M UTC"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Booking email failed for appointment #%s: %s",
                appointment.pk,
                exc,
            )
