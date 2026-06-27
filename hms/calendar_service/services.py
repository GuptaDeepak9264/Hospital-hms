"""
Google Calendar service.

Flow:
  1. User visits /api/calendar/authorize/ → redirected to Google consent page.
  2. Google redirects back to /api/calendar/oauth2/callback/?code=...
  3. We exchange the code for tokens and store them in GoogleOAuth2Credential.
  4. On booking, CalendarService.create_booking_events() creates events in
     both the doctor's and patient's Google Calendars (if they have connected).
"""

import json
import logging

from django.conf import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from accounts.models import User
from calendar_service.models import GoogleOAuth2Credential

logger = logging.getLogger(__name__)


def _build_flow() -> Flow:
    """Construct a google_auth_oauthlib Flow from Django settings."""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_OAUTH2_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=settings.GOOGLE_CALENDAR_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH2_REDIRECT_URI,
    )


def get_authorization_url() -> tuple[str, str]:
    """Return (authorization_url, state) to redirect the user to Google."""
    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url, state


def exchange_code_for_credentials(code: str) -> Credentials:
    """Exchange the OAuth2 authorization code for a Credentials object."""
    flow = _build_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def save_credentials(user: User, credentials: Credentials) -> None:
    """Persist Google OAuth2 credentials to the database."""
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else [],
    }
    GoogleOAuth2Credential.objects.update_or_create(
        user=user,
        defaults={"token_json": json.dumps(token_data)},
    )
    logger.info("Saved Google credentials for user %s", user.email)


def load_credentials(user: User) -> Credentials | None:
    """Load and (if necessary) refresh stored Google OAuth2 credentials."""
    try:
        record = GoogleOAuth2Credential.objects.get(user=user)
    except GoogleOAuth2Credential.DoesNotExist:
        return None

    data = json.loads(record.token_json)
    credentials = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes", settings.GOOGLE_CALENDAR_SCOPES),
    )

    # Refresh token if expired
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            save_credentials(user, credentials)
        except Exception as exc:
            logger.warning("Failed to refresh credentials for %s: %s", user.email, exc)
            return None

    return credentials


class CalendarService:
    """Creates Google Calendar events for appointments."""

    @staticmethod
    def create_booking_events(appointment) -> None:
        """
        Create a calendar event in both the doctor's and patient's calendars.
        Silently skips users who haven't connected their Google Calendar.
        """
        slot = appointment.availability
        doctor_user = slot.doctor.user
        patient_user = appointment.patient.user

        event_body = {
            "summary": f"HMS Appointment — Dr. {doctor_user.get_full_name()} & {patient_user.get_full_name()}",
            "description": (
                f"Hospital Management System Appointment\n\n"
                f"Doctor: Dr. {doctor_user.get_full_name()}\n"
                f"Patient: {patient_user.get_full_name()}\n"
                f"Date: {slot.start_time.strftime('%Y-%m-%d')}\n"
                f"Time: {slot.start_time.strftime('%H:%M')} — {slot.end_time.strftime('%H:%M')} UTC\n"
                f"Notes: {appointment.notes or 'None'}"
            ),
            "start": {
                "dateTime": slot.start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": slot.end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        # Create event in doctor's calendar
        doctor_event_id = CalendarService._create_event(doctor_user, event_body)
        if doctor_event_id:
            appointment.doctor_calendar_event_id = doctor_event_id

        # Create event in patient's calendar
        patient_event_id = CalendarService._create_event(patient_user, event_body)
        if patient_event_id:
            appointment.patient_calendar_event_id = patient_event_id

        # Persist event IDs without triggering a full save cycle
        appointment.save(
            update_fields=["doctor_calendar_event_id", "patient_calendar_event_id", "updated_at"]
        )

    @staticmethod
    def _create_event(user: User, event_body: dict) -> str | None:
        """
        Create a single Google Calendar event for the given user.
        Returns the event ID on success, None if the user has no credentials.
        """
        credentials = load_credentials(user)
        if not credentials:
            logger.info(
                "No Google credentials for %s — skipping calendar event.", user.email
            )
            return None

        try:
            service = build("calendar", "v3", credentials=credentials)
            event = service.events().insert(calendarId="primary", body=event_body).execute()
            logger.info("Calendar event %s created for user %s", event["id"], user.email)
            return event["id"]
        except HttpError as exc:
            logger.error(
                "Google Calendar API error for user %s: %s", user.email, exc
            )
            return None
