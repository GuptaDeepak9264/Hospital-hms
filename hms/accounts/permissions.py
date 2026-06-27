"""
Custom DRF permission classes enforcing role-based access control.

  IsDoctorUser  — only authenticated doctors may proceed.
  IsPatientUser — only authenticated patients may proceed.

These are used as view-level permissions and also importable as decorators
via the @doctor_required / @patient_required helpers in accounts/decorators.py.
"""

from rest_framework.permissions import BasePermission


class IsDoctorUser(BasePermission):
    """Allow access only to users with role == 'doctor'."""

    message = "Access restricted to doctors only."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_doctor
        )


class IsPatientUser(BasePermission):
    """Allow access only to users with role == 'patient'."""

    message = "Access restricted to patients only."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_patient
        )
