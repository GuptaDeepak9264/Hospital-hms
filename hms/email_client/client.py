"""
Email service client.

Django calls this module to trigger email delivery via the separate
serverless email microservice (email-service/handler.py running on
serverless-offline at localhost:3001).

All calls are synchronous HTTP POST requests. Failures are handled
gracefully — a broken email service must NOT impact core booking flow.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Base URL for the serverless email service (configurable via .env)
EMAIL_SERVICE_BASE_URL: str = ""


def _get_base_url() -> str:
    """Return the email service base URL from settings (lazy lookup)."""
    return settings.EMAIL_SERVICE_URL.rstrip("/")


class EmailServiceClient:
    """
    Thin HTTP client that posts to the serverless email service.
    Each static method maps to one email trigger type.
    """

    TIMEOUT_SECONDS = 10  # Don't let a slow email service block Django

    @staticmethod
    def _post(endpoint: str, payload: dict) -> bool:
        """
        POST payload to the serverless email service endpoint.
        Returns True on success, False on any error.
        """
        url = f"{_get_base_url()}{endpoint}"
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=EmailServiceClient.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            logger.info("Email service call to %s succeeded.", url)
            return True
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Email service unreachable at %s. "
                "Is serverless-offline running? (npm run offline)",
                url,
            )
            return False
        except requests.exceptions.Timeout:
            logger.warning("Email service timed out at %s.", url)
            return False
        except requests.exceptions.HTTPError as exc:
            logger.error("Email service HTTP error at %s: %s", url, exc)
            return False
        except Exception as exc:  # noqa: BLE001
            logger.error("Email service unexpected error: %s", exc)
            return False

    @staticmethod
    def send_signup_welcome(recipient_email: str, recipient_name: str) -> bool:
        """
        Trigger SIGNUP_WELCOME email.
        Called immediately after a new user account is created.
        """
        return EmailServiceClient._post(
            "/dev/email/send",
            {
                "trigger": "SIGNUP_WELCOME",
                "recipient_email": recipient_email,
                "recipient_name": recipient_name,
            },
        )

    @staticmethod
    def send_booking_confirmation(
        recipient_email: str,
        recipient_name: str,
        doctor_name: str,
        appointment_datetime: str,
    ) -> bool:
        """
        Trigger BOOKING_CONFIRMATION email.
        Called after a successful appointment booking.
        """
        return EmailServiceClient._post(
            "/dev/email/send",
            {
                "trigger": "BOOKING_CONFIRMATION",
                "recipient_email": recipient_email,
                "recipient_name": recipient_name,
                "doctor_name": doctor_name,
                "appointment_datetime": appointment_datetime,
            },
        )
