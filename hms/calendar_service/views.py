"""
Google Calendar OAuth2 views.

GET  /api/calendar/authorize/         — start OAuth2 flow (returns redirect URL)
GET  /api/calendar/oauth2/callback/   — Google redirects here with auth code
GET  /api/calendar/status/            — check if current user has connected calendar
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from calendar_service.models import GoogleOAuth2Credential
from calendar_service.services import (
    get_authorization_url,
    exchange_code_for_credentials,
    save_credentials,
)

logger = logging.getLogger(__name__)


class CalendarAuthorizeView(APIView):
    """
    GET /api/calendar/authorize/
    Returns a Google OAuth2 URL that the client should redirect the user to.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            authorization_url, state = get_authorization_url()
            # Store state in session for CSRF protection
            request.session["google_oauth2_state"] = state
        except Exception as exc:
            logger.error("Failed to build Google authorization URL: %s", exc)
            return Response(
                {
                    "success": False,
                    "message": "Google Calendar integration is not configured. "
                               "Please set GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "success": True,
                "data": {
                    "authorization_url": authorization_url,
                    "message": "Redirect the user to authorization_url to connect Google Calendar.",
                },
            }
        )


class CalendarOAuth2CallbackView(APIView):
    """
    GET /api/calendar/oauth2/callback/?code=...&state=...
    Google redirects here after the user grants consent.
    We exchange the code for tokens and persist them.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = request.query_params.get("code")
        error = request.query_params.get("error")

        if error:
            return Response(
                {
                    "success": False,
                    "message": f"Google OAuth2 authorization denied: {error}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not code:
            return Response(
                {"success": False, "message": "Authorization code not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            credentials = exchange_code_for_credentials(code)
            save_credentials(request.user, credentials)
        except Exception as exc:
            logger.error(
                "OAuth2 token exchange failed for user %s: %s",
                request.user.email,
                exc,
            )
            return Response(
                {
                    "success": False,
                    "message": "Failed to exchange authorization code. Please try again.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Google Calendar connected successfully! "
                           "Calendar events will be created for future bookings.",
            }
        )


class CalendarStatusView(APIView):
    """
    GET /api/calendar/status/
    Returns whether the current user has a connected Google Calendar.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_connected = GoogleOAuth2Credential.objects.filter(user=request.user).exists()
        return Response(
            {
                "success": True,
                "data": {
                    "google_calendar_connected": is_connected,
                    "user_email": request.user.email,
                },
            }
        )


class CalendarDisconnectView(APIView):
    """
    DELETE /api/calendar/disconnect/
    Removes stored Google OAuth2 credentials for the current user.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        deleted_count, _ = GoogleOAuth2Credential.objects.filter(
            user=request.user
        ).delete()

        if deleted_count == 0:
            return Response(
                {"success": False, "message": "No Google Calendar connection found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"success": True, "message": "Google Calendar disconnected successfully."}
        )
