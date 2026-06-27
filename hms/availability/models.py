"""
DoctorAvailability model.
Represents a time slot a doctor is available for consultation.
One availability row = one bookable slot.
"""

from django.db import models
from django.utils import timezone

from doctors.models import Doctor


class DoctorAvailability(models.Model):
    """
    A single, bookable time slot owned by a doctor.

    Business rules enforced at the service/serializer layer:
     - start_time must be in the future
     - end_time must be after start_time
     - no overlapping slots for the same doctor
     - once booked (is_booked=True), cannot be booked again
    """

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False, db_index=True)
    notes = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctor_availability"
        verbose_name = "Doctor Availability"
        verbose_name_plural = "Doctor Availability Slots"
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["doctor", "start_time", "end_time"]),
            models.Index(fields=["doctor", "is_booked"]),
        ]

    def __str__(self) -> str:
        status = "BOOKED" if self.is_booked else "AVAILABLE"
        return (
            f"Dr.{self.doctor.user.get_full_name()} | "
            f"{self.start_time:%Y-%m-%d %H:%M} → {self.end_time:%H:%M} [{status}]"
        )

    @property
    def is_past(self) -> bool:
        return self.start_time < timezone.now()

    @property
    def duration_minutes(self) -> int:
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
