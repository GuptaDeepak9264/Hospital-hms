"""
GoogleOAuth2Credential model.
Stores per-user Google OAuth2 tokens so we can create calendar events
on behalf of doctors and patients without re-authorising each time.
"""

from django.db import models
from accounts.models import User


class GoogleOAuth2Credential(models.Model):
    """
    Persists a user's Google OAuth2 token in the database.
    The token JSON is stored as text (contains access_token, refresh_token, etc.).
    Sensitive — restrict DB access accordingly in production.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="google_oauth2_credential",
    )
    token_json = models.TextField(
        help_text="Serialised google.oauth2.credentials.Credentials JSON"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "google_oauth2_credentials"
        verbose_name = "Google OAuth2 Credential"
        verbose_name_plural = "Google OAuth2 Credentials"

    def __str__(self) -> str:
        return f"OAuth2 credential for {self.user.email}"
