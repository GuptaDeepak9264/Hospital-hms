"""
Doctor-facing API views.
All endpoints are protected by IsDoctorUser permission.
Doctors can only see / modify their own data.
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsDoctorUser
from doctors.models import Doctor
from doctors.serializers import DoctorProfileSerializer, DoctorProfileUpdateSerializer
from appointments.serializers import AppointmentDetailSerializer
from appointments.models import Appointment

logger = logging.getLogger(__name__)


class DoctorDashboardView(APIView):
    """
    GET /api/doctors/dashboard/
    Returns profile + upcoming bookings summary for the authenticated doctor.
    """

    permission_classes = [IsDoctorUser]

    def get(self, request):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return Response(
                {"success": False, "message": "Doctor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        upcoming_appointments = Appointment.objects.filter(
            availability__doctor=doctor,
            status="confirmed",
        ).select_related("patient__user", "availability").order_by(
            "availability__start_time"
        )

        return Response(
            {
                "success": True,
                "data": {
                    "profile": DoctorProfileSerializer(doctor).data,
                    "upcoming_appointments_count": upcoming_appointments.count(),
                },
            },
            status=status.HTTP_200_OK,
        )


class DoctorProfileView(APIView):
    """
    GET  /api/doctors/profile/   — read own profile
    PUT  /api/doctors/profile/   — update own profile
    PATCH /api/doctors/profile/  — partial update
    """

    permission_classes = [IsDoctorUser]

    def get(self, request):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return Response(
                {"success": False, "message": "Doctor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"success": True, "data": DoctorProfileSerializer(doctor).data},
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial: bool):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return Response(
                {"success": False, "message": "Doctor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DoctorProfileUpdateSerializer(
            doctor, data=request.data, partial=partial
        )
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "data": DoctorProfileSerializer(doctor).data,
            },
            status=status.HTTP_200_OK,
        )


class DoctorBookingsView(APIView):
    """
    GET /api/doctors/bookings/
    Returns all bookings for the authenticated doctor (own bookings only).
    """

    permission_classes = [IsDoctorUser]

    def get(self, request):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return Response(
                {"success": False, "message": "Doctor profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        appointments = (
            Appointment.objects.filter(availability__doctor=doctor)
            .select_related("patient__user", "availability")
            .order_by("-created_at")
        )

        return Response(
            {
                "success": True,
                "data": AppointmentDetailSerializer(appointments, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
