"""
Patient-facing API views.
All endpoints protected by IsPatientUser permission.
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsPatientUser
from doctors.models import Doctor
from doctors.serializers import DoctorListSerializer
from patients.models import Patient
from patients.serializers import PatientProfileSerializer, PatientProfileUpdateSerializer
from appointments.models import Appointment
from appointments.serializers import AppointmentDetailSerializer

logger = logging.getLogger(__name__)


class PatientDashboardView(APIView):
    """
    GET /api/patients/dashboard/
    Returns patient profile and a booking summary.
    """

    permission_classes = [IsPatientUser]

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "message": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        total_bookings = Appointment.objects.filter(patient=patient).count()

        return Response(
            {
                "success": True,
                "data": {
                    "profile": PatientProfileSerializer(patient).data,
                    "total_bookings": total_bookings,
                },
            },
            status=status.HTTP_200_OK,
        )


class PatientProfileView(APIView):
    """
    GET   /api/patients/profile/  — read own profile
    PUT   /api/patients/profile/  — full update
    PATCH /api/patients/profile/  — partial update
    """

    permission_classes = [IsPatientUser]

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "message": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"success": True, "data": PatientProfileSerializer(patient).data},
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        return self._update(request, partial=False)

    def patch(self, request):
        return self._update(request, partial=True)

    def _update(self, request, partial: bool):
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "message": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PatientProfileUpdateSerializer(
            patient, data=request.data, partial=partial
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
                "message": "Profile updated.",
                "data": PatientProfileSerializer(patient).data,
            },
            status=status.HTTP_200_OK,
        )


class PatientDoctorListView(APIView):
    """
    GET /api/patients/doctors/
    Returns all registered doctors (for patients to browse).
    """

    permission_classes = [IsPatientUser]

    def get(self, request):
        doctors = Doctor.objects.select_related("user").filter(user__is_active=True)
        return Response(
            {
                "success": True,
                "data": DoctorListSerializer(doctors, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class PatientBookingHistoryView(APIView):
    """
    GET /api/patients/bookings/
    Returns all appointments for the authenticated patient.
    """

    permission_classes = [IsPatientUser]

    def get(self, request):
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "message": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        appointments = (
            Appointment.objects.filter(patient=patient)
            .select_related("availability__doctor__user")
            .order_by("-created_at")
        )

        return Response(
            {
                "success": True,
                "data": AppointmentDetailSerializer(appointments, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
