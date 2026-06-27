"""
Serializers for the Doctor profile and dashboard data.
"""

from rest_framework import serializers
from doctors.models import Doctor
from accounts.serializers import UserSerializer


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Full doctor profile (used for dashboard and self-view)."""

    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            "id",
            "user",
            "full_name",
            "specialization",
            "qualification",
            "experience_years",
            "consultation_fee",
            "bio",
            "created_at",
            "updated_at",
        ]

    def get_full_name(self, obj: Doctor) -> str:
        return obj.user.get_full_name()


class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    """Allows a doctor to update their own profile details."""

    class Meta:
        model = Doctor
        fields = [
            "specialization",
            "qualification",
            "experience_years",
            "consultation_fee",
            "bio",
        ]


class DoctorListSerializer(serializers.ModelSerializer):
    """
    Minimal doctor representation shown to patients when browsing.
    Excludes any internal / sensitive fields.
    """

    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Doctor
        fields = [
            "id",
            "full_name",
            "email",
            "specialization",
            "qualification",
            "experience_years",
            "consultation_fee",
            "bio",
        ]

    def get_full_name(self, obj: Doctor) -> str:
        return obj.user.get_full_name()
