"""
Custom decorators for role-based access control on CBV dispatch methods.

Usage (inside a dispatch override or on a function view):
    @doctor_required
    def my_view(request, *args, **kwargs): ...
"""

from functools import wraps

from rest_framework.response import Response
from rest_framework import status


def doctor_required(func):
    """Decorator that blocks non-doctor authenticated users."""

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"success": False, "message": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not request.user.is_doctor:
            return Response(
                {"success": False, "message": "Access restricted to doctors only."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return func(request, *args, **kwargs)

    return wrapper


def patient_required(func):
    """Decorator that blocks non-patient authenticated users."""

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"success": False, "message": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not request.user.is_patient:
            return Response(
                {"success": False, "message": "Access restricted to patients only."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return func(request, *args, **kwargs)

    return wrapper
