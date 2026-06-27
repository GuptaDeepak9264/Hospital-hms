from django.urls import path
from patients.views import (
    PatientDashboardView,
    PatientProfileView,
    PatientDoctorListView,
    PatientBookingHistoryView,
)

urlpatterns = [
    path("dashboard/", PatientDashboardView.as_view(), name="patient-dashboard"),
    path("profile/", PatientProfileView.as_view(), name="patient-profile"),
    path("doctors/", PatientDoctorListView.as_view(), name="patient-doctor-list"),
    path("bookings/", PatientBookingHistoryView.as_view(), name="patient-booking-history"),
]
