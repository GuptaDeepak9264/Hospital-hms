"""
Service layer for availability slot management.
Overlap detection ensures no two slots for the same doctor share time.
"""

import logging

from django.db import transaction
from django.db.models import Q

from availability.models import DoctorAvailability
from doctors.models import Doctor

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Handles creation, update, and deletion of doctor availability slots."""

    @staticmethod
    def _check_overlap(
        doctor: Doctor,
        start_time,
        end_time,
        exclude_id: int = None,
    ) -> bool:
        """
        Returns True if the proposed [start_time, end_time] window overlaps
        any existing slot for the given doctor.

        Overlap condition (two intervals A and B overlap when):
            A.start < B.end AND A.end > B.start
        """
        qs = DoctorAvailability.objects.filter(
            doctor=doctor,
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    @classmethod
    @transaction.atomic
    def create_slot(cls, doctor: Doctor, validated_data: dict) -> DoctorAvailability:
        start = validated_data["start_time"]
        end = validated_data["end_time"]

        if cls._check_overlap(doctor, start, end):
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                "This slot overlaps with an existing availability slot."
            )

        slot = DoctorAvailability.objects.create(
            doctor=doctor,
            start_time=start,
            end_time=end,
            notes=validated_data.get("notes", ""),
        )
        logger.info("Created availability slot %s for Dr. %s", slot.id, doctor.user.email)
        return slot

    @classmethod
    @transaction.atomic
    def update_slot(
        cls,
        slot: DoctorAvailability,
        validated_data: dict,
    ) -> DoctorAvailability:
        if slot.is_booked:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot edit a slot that has already been booked.")

        start = validated_data.get("start_time", slot.start_time)
        end = validated_data.get("end_time", slot.end_time)

        if cls._check_overlap(slot.doctor, start, end, exclude_id=slot.pk):
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                "The updated slot overlaps with an existing availability slot."
            )

        for field, value in validated_data.items():
            setattr(slot, field, value)
        slot.save()
        return slot

    @staticmethod
    @transaction.atomic
    def delete_slot(slot: DoctorAvailability) -> None:
        if slot.is_booked:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete a slot that has already been booked.")
        slot.delete()
