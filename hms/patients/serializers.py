"""Serializers for the Patient profile."""

from rest_framework import serializers
from patients.models import Patient
from accounts.serializers import UserSerializer


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id", "user", "full_name", "date_of_birth", "gender",
            "blood_group", "phone", "address", "medical_history",
            "created_at", "updated_at",
        ]

    def get_full_name(self, obj: Patient) -> str:
        return obj.user.get_full_name()


class PatientProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["date_of_birth", "gender", "blood_group", "phone", "address", "medical_history"]
