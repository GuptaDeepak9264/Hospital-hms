from django.urls import path
from availability.views import (
    AvailabilityListCreateView,
    AvailabilityDetailView,
    PatientDoctorAvailabilityView,
)

urlpatterns = [
    # Doctor endpoints
    path("", AvailabilityListCreateView.as_view(), name="availability-list-create"),
    path("<int:pk>/", AvailabilityDetailView.as_view(), name="availability-detail"),

    # Patient endpoint — browse a doctor's open future slots
    path(
        "doctor/<int:doctor_id>/",
        PatientDoctorAvailabilityView.as_view(),
        name="patient-doctor-availability",
    ),
]
