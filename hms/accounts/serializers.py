"""
Serializers for user authentication: signup, login, and user representation.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.models import User, UserRole


class SignupSerializer(serializers.ModelSerializer):
    """
    Handles user registration for both Doctor and Patient roles.
    Password is write-only and hashed before storage.
    """

    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRole.choices)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "password"]
        read_only_fields = ["id"]

    def validate_email(self, value: str) -> str:
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )


class LoginSerializer(serializers.Serializer):
    """Validates login credentials and returns the authenticated user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs.get("email", "").lower().strip()
        password = attrs.get("password", "")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            raise serializers.ValidationError(
                "Invalid credentials. Please check your email and password."
            )
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")

        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user (used in API responses)."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "role", "date_joined"]

    def get_full_name(self, obj: User) -> str:
        return obj.get_full_name()
