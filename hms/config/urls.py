"""
Root URL configuration for the Hospital Management System.
All API routes are versioned under /api/v1/.
"""

from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentication endpoints
    path("api/auth/", include("accounts.urls")),

    # Doctor endpoints
    path("api/doctors/", include("doctors.urls")),

    # Patient endpoints
    path("api/patients/", include("patients.urls")),

    # Availability endpoints (doctor manages their slots)
    path("api/availability/", include("availability.urls")),

    # Appointment / booking endpoints
    path("api/appointments/", include("appointments.urls")),

    # Google Calendar OAuth2 + event endpoints
    path("api/calendar/", include("calendar_service.urls")),
]
