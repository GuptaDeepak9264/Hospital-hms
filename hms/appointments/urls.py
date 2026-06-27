from django.urls import path
from appointments.views import BookAppointmentView, AppointmentDetailView

urlpatterns = [
    path("book/", BookAppointmentView.as_view(), name="appointment-book"),
    path("<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
]
