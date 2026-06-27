"""
Serializers for Appointment model.
"""

from rest_framework import serializers

from appointments.models import Appointment
from availability.serializers import AvailabilitySerializer
from patients.serializers import PatientProfileSerializer


class AppointmentBookSerializer(serializers.Serializer):
    """Input serializer for booking a slot. Only needs availability_id."""

    availability_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Full appointment detail returned after booking or in history views."""

    availability = AvailabilitySerializer(read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    appointment_date = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient_name",
            "doctor_name",
            "appointment_date",
            "availability",
            "status",
            "notes",
            "doctor_calendar_event_id",
            "patient_calendar_event_id",
            "created_at",
            "updated_at",
        ]

    def get_patient_name(self, obj: Appointment) -> str:
        return obj.patient.user.get_full_name()

    def get_doctor_name(self, obj: Appointment) -> str:
        return obj.availability.doctor.user.get_full_name()

    def get_appointment_date(self, obj: Appointment) -> str:
        return obj.availability.start_time.strftime("%Y-%m-%d %H:%M UTC")
