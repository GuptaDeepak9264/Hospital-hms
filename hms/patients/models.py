"""
Patient profile model.
Extended profile for users with role='patient'.
"""

from django.db import models
from accounts.models import User


class Patient(models.Model):
    """Extended profile for users with role='patient'."""

    BLOOD_GROUP_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        limit_choices_to={"role": "patient"},
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        blank=True,
        default="",
    )
    blood_group = models.CharField(
        max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, default=""
    )
    phone = models.CharField(max_length=20, blank=True, default="")
    address = models.TextField(blank=True, default="")
    medical_history = models.TextField(blank=True, default="")

    # Google Calendar token path for the patient
    google_calendar_token_path = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "patients"
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self) -> str:
        return f"Patient: {self.user.get_full_name()} <{self.user.email}>"
