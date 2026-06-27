from django.urls import path
from calendar_service.views import (
    CalendarAuthorizeView,
    CalendarOAuth2CallbackView,
    CalendarStatusView,
    CalendarDisconnectView,
)

urlpatterns = [
    path("authorize/", CalendarAuthorizeView.as_view(), name="calendar-authorize"),
    path("oauth2/callback/", CalendarOAuth2CallbackView.as_view(), name="calendar-callback"),
    path("status/", CalendarStatusView.as_view(), name="calendar-status"),
    path("disconnect/", CalendarDisconnectView.as_view(), name="calendar-disconnect"),
]
