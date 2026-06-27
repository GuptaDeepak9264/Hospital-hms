"""
Service layer for authentication.
Keeps business logic out of views — views remain thin orchestrators.
"""

import logging

from django.contrib.auth import login, logout
from django.db import transaction

from accounts.models import User
from accounts.serializers import SignupSerializer
from email_client.client import EmailServiceClient

logger = logging.getLogger(__name__)


class AuthService:
    """Encapsulates all authentication-related business logic."""

    @staticmethod
    @transaction.atomic
    def signup(validated_data: dict, request) -> User:
        """
        Create a new user account and trigger a welcome email.
        Wrapped in a transaction so partial failure rolls back cleanly.
        """
        serializer = SignupSerializer(data=validated_data)
        serializer.is_valid(raise_exception=True)
        user: User = serializer.save()

        # Authenticate the new session immediately
        login(request, user)

        # Fire-and-forget welcome email via the serverless email service
        try:
            EmailServiceClient.send_signup_welcome(
                recipient_email=user.email,
                recipient_name=user.get_full_name(),
            )
        except Exception as exc:  # noqa: BLE001
            # Email failure should NOT roll back user creation
            logger.warning("Welcome email failed for %s: %s", user.email, exc)

        return user

    @staticmethod
    def login_user(user: User, request) -> None:
        """Persist the authenticated session."""
        login(request, user)

    @staticmethod
    def logout_user(request) -> None:
        """Flush the session."""
        logout(request)
