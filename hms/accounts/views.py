"""
Authentication views: Signup, Login, Logout, and current-user info.
All views return a consistent JSON envelope.
"""

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import LoginSerializer, UserSerializer
from accounts.services import AuthService

logger = logging.getLogger(__name__)


class SignupView(APIView):
    """
    POST /api/auth/signup/
    Open endpoint — no authentication required.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user = AuthService.signup(request.data, request)
        except Exception as exc:
            logger.error("Signup failed: %s", exc)
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": "Account created successfully. Welcome to HMS!",
                "data": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/
    Open endpoint — no authentication required.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Invalid credentials.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data["user"]
        AuthService.login_user(user, request)

        return Response(
            {
                "success": True,
                "message": "Logged in successfully.",
                "data": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        AuthService.logout_user(request)
        return Response(
            {"success": True, "message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns the currently authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "data": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )
