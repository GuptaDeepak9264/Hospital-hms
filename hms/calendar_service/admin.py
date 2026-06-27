from django.contrib import admin
from calendar_service.models import GoogleOAuth2Credential


@admin.register(GoogleOAuth2Credential)
class GoogleOAuth2CredentialAdmin(admin.ModelAdmin):
    list_display = ["user", "created_at", "updated_at"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at"]
    # Hide raw token from list to protect sensitive data
    exclude = ["token_json"]
