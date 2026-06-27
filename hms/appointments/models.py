"""
Appointment model.

One appointment ties one Patient to one DoctorAvailability slot.
The slot is marked is_booked=True atomically during the booking transaction.
"""

from django.db import models

from availability.models import DoctorAvailability
from patients.models import Patient


class AppointmentStatus(models.TextChoices):
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class Appointment(models.Model):
    """
    Core booking record.

    The atomic locking is performed in AppointmentService.book_slot():
      1. select_for_update() acquires a row-level lock on the slot.
      2. Re-check is_booked inside the transaction.
      3. Set is_booked=True and create Appointment — all in one atomic block.
    """

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    availability = models.OneToOneField(
        DoctorAvailability,
        on_delete=models.CASCADE,
        related_name="appointment",
    )
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.CONFIRMED,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")

    # Google Calendar event IDs (stored after successful calendar event creation)
    doctor_calendar_event_id = models.CharField(max_length=255, blank=True, default="")
    patient_calendar_event_id = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"Appt#{self.pk} | {self.patient.user.get_full_name()} → "
            f"Dr.{self.availability.doctor.user.get_full_name()} | "
            f"{self.availability.start_time:%Y-%m-%d %H:%M} [{self.status}]"
        )
