"""
Availability views.

Doctor endpoints (IsDoctorUser):
  POST   /api/availability/           — create slot
  GET    /api/availability/           — list own slots
  GET    /api/availability/<id>/      — retrieve own slot
  PUT    /api/availability/<id>/      — full update
  PATCH  /api/availability/<id>/      — partial update
  DELETE /api/availability/<id>/      — delete (if not booked)

Patient endpoints (IsPatientUser):
  GET    /api/availability/doctor/<doctor_id>/  — browse a doctor's future open slots
"""

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsDoctorUser, IsPatientUser
from availability.models import DoctorAvailability
from availability.serializers import (
    AvailabilitySerializer,
    AvailabilityCreateSerializer,
    AvailabilityUpdateSerializer,
)
from availability.services import AvailabilityService
from doctors.models import Doctor

logger = logging.getLogger(__name__)


class AvailabilityListCreateView(APIView):
    """
    GET  /api/availability/  — doctor lists their own slots
    POST /api/availability/  — doctor creates a new slot
    """

    permission_classes = [IsDoctorUser]

    def get(self, request):
        doctor = request.user.doctor_profile
        slots = DoctorAvailability.objects.filter(doctor=doctor).order_by("start_time")
        return Response(
            {
                "success": True,
                "data": AvailabilitySerializer(slots, many=True).data,
            }
        )

    def post(self, request):
        doctor = request.user.doctor_profile
        serializer = AvailabilityCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            slot = AvailabilityService.create_slot(doctor, serializer.validated_data)
        except Exception as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "message": "Availability slot created.",
                "data": AvailabilitySerializer(slot).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AvailabilityDetailView(APIView):
    """
    GET    /api/availability/<id>/  — retrieve
    PUT    /api/availability/<id>/  — update
    PATCH  /api/availability/<id>/  — partial update
    DELETE /api/availability/<id>/  — delete
    """

    permission_classes = [IsDoctorUser]

    def _get_own_slot(self, request, pk: int) -> DoctorAvailability:
        doctor = request.user.doctor_profile
        return get_object_or_404(DoctorAvailability, pk=pk, doctor=doctor)

    def get(self, request, pk: int):
        slot = self._get_own_slot(request, pk)
        return Response({"success": True, "data": AvailabilitySerializer(slot).data})

    def put(self, request, pk: int):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk: int):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk: int, partial: bool):
        slot = self._get_own_slot(request, pk)
        serializer = AvailabilityUpdateSerializer(slot, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            updated_slot = AvailabilityService.update_slot(slot, serializer.validated_data)
        except Exception as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "success": True,
                "message": "Availability slot updated.",
                "data": AvailabilitySerializer(updated_slot).data,
            }
        )

    def delete(self, request, pk: int):
        slot = self._get_own_slot(request, pk)
        try:
            AvailabilityService.delete_slot(slot)
        except Exception as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"success": True, "message": "Availability slot deleted."},
            status=status.HTTP_200_OK,
        )


class PatientDoctorAvailabilityView(APIView):
    """
    GET /api/availability/doctor/<doctor_id>/
    Returns future, unbooked slots for a specific doctor.
    Accessible by patients only.
    """

    permission_classes = [IsPatientUser]

    def get(self, request, doctor_id: int):
        doctor = get_object_or_404(Doctor, pk=doctor_id, user__is_active=True)
        slots = DoctorAvailability.objects.filter(
            doctor=doctor,
            is_booked=False,
            start_time__gt=timezone.now(),
        ).order_by("start_time")

        return Response(
            {
                "success": True,
                "data": AvailabilitySerializer(slots, many=True).data,
            }
        )
