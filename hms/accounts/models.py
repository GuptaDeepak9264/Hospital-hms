"""
Custom User model for HMS.

Roles:
  DOCTOR  — clinician who creates availability and receives bookings.
  PATIENT — end-user who books appointments.

We extend AbstractBaseUser + PermissionsMixin so we control everything while
still being compatible with Django's auth framework.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    DOCTOR = "doctor", "Doctor"
    PATIENT = "patient", "Patient"


class UserManager(BaseUserManager):
    """Custom manager so we can create users with email as the unique identifier."""

    def _create_user(self, email: str, password: str, role: str, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        if not role:
            raise ValueError("Role is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)  # hashes via PBKDF2 by default
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str, role: str, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, role, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        role = extra_fields.pop("role", UserRole.DOCTOR)
        return self._create_user(email, password, role, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Central user model shared by both doctors and patients.
    Profile details live in the Doctors / Patients app models.
    """

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=10, choices=UserRole.choices)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}> [{self.role}]"

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_doctor(self) -> bool:
        return self.role == UserRole.DOCTOR

    @property
    def is_patient(self) -> bool:
        return self.role == UserRole.PATIENT
