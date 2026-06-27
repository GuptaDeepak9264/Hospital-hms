from django.urls import path
from doctors.views import DoctorDashboardView, DoctorProfileView, DoctorBookingsView

urlpatterns = [
    path("dashboard/", DoctorDashboardView.as_view(), name="doctor-dashboard"),
    path("profile/", DoctorProfileView.as_view(), name="doctor-profile"),
    path("bookings/", DoctorBookingsView.as_view(), name="doctor-bookings"),
]
