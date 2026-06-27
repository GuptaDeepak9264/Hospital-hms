"""
Appointment (booking) views.

POST /api/appointments/book/    — patient books a slot
GET  /api/appointments/<id>/    — retrieve appointment detail (patient or doctor)
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from accounts.permissions import IsPatientUser
from appointments.models import Appointment
from appointments.serializers import AppointmentBookSerializer, AppointmentDetailSerializer
from appointments.services import AppointmentService
from patients.models import Patient

logger = logging.getLogger(__name__)


class BookAppointmentView(APIView):
    """
    POST /api/appointments/book/
    Patient books an available slot. Race-condition safe.
    """

    permission_classes = [IsPatientUser]

    def post(self, request):
        serializer = AppointmentBookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response(
                {"success": False, "message": "Patient profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            appointment = AppointmentService.book_slot(
                patient=patient,
                availability_id=serializer.validated_data["availability_id"],
                notes=serializer.validated_data.get("notes", ""),
            )
        except Exception as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "success": True,
                "message": "Appointment booked successfully!",
                "data": AppointmentDetailSerializer(appointment).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AppointmentDetailView(APIView):
    """
    GET /api/appointments/<id>/
    Returns appointment detail. Accessible by the owning patient or the doctor.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        user = request.user

        if user.is_patient:
            try:
                patient = user.patient_profile
            except Patient.DoesNotExist:
                return Response(
                    {"success": False, "message": "Patient profile not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            appointment = get_object_or_404(Appointment, pk=pk, patient=patient)

        elif user.is_doctor:
            appointment = get_object_or_404(
                Appointment, pk=pk, availability__doctor=user.doctor_profile
            )
        else:
            return Response(
                {"success": False, "message": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "success": True,
                "data": AppointmentDetailSerializer(appointment).data,
            }
        )
