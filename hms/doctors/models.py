"""
Doctor profile model.
Extends the base User via a OneToOne relationship.
"""

from django.db import models
from accounts.models import User


class Doctor(models.Model):
    """
    Extended profile for users with role='doctor'.
    Created automatically after signup via a signal (see doctors/signals.py).
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
        limit_choices_to={"role": "doctor"},
    )
    specialization = models.CharField(max_length=200, blank=True, default="")
    qualification = models.CharField(max_length=300, blank=True, default="")
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    bio = models.TextField(blank=True, default="")

    # Google Calendar credentials stored as a JSON string path
    google_calendar_token_path = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctors"
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self) -> str:
        return f"Dr. {self.user.get_full_name()} — {self.specialization}"
