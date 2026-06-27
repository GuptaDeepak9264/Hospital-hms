"""
Serializers for DoctorAvailability.
Validate business rules (no past slots, end > start, no overlaps).
"""

from django.utils import timezone
from rest_framework import serializers

from availability.models import DoctorAvailability


class AvailabilitySerializer(serializers.ModelSerializer):
    """Full representation returned in GET responses."""

    doctor_name = serializers.SerializerMethodField()
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = DoctorAvailability
        fields = [
            "id",
            "doctor",
            "doctor_name",
            "start_time",
            "end_time",
            "duration_minutes",
            "is_booked",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "doctor", "is_booked", "created_at", "updated_at"]

    def get_doctor_name(self, obj: DoctorAvailability) -> str:
        return obj.doctor.user.get_full_name()


class AvailabilityCreateSerializer(serializers.ModelSerializer):
    """Used when a doctor creates a new availability slot."""

    class Meta:
        model = DoctorAvailability
        fields = ["start_time", "end_time", "notes"]

    def validate_start_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "Start time must be in the future."
            )
        return value

    def validate(self, attrs):
        start = attrs.get("start_time")
        end = attrs.get("end_time")

        if end is None:
            raise serializers.ValidationError({"end_time": "End time is required."})

        if end <= start:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )

        # Minimum slot duration: 15 minutes
        delta_minutes = (end - start).total_seconds() / 60
        if delta_minutes < 15:
            raise serializers.ValidationError(
                {"end_time": "Slot duration must be at least 15 minutes."}
            )

        return attrs


class AvailabilityUpdateSerializer(serializers.ModelSerializer):
    """Used when a doctor edits an existing (non-booked) slot."""

    class Meta:
        model = DoctorAvailability
        fields = ["start_time", "end_time", "notes"]

    def validate(self, attrs):
        instance: DoctorAvailability = self.instance

        if instance and instance.is_booked:
            raise serializers.ValidationError(
                "Cannot edit a slot that has already been booked."
            )

        start = attrs.get("start_time", instance.start_time if instance else None)
        end = attrs.get("end_time", instance.end_time if instance else None)

        if start and start <= timezone.now():
            raise serializers.ValidationError(
                {"start_time": "Start time must be in the future."}
            )
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )

        return attrs
