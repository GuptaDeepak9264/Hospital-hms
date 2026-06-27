from django.contrib import admin
from patients.models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["user", "gender", "blood_group", "phone"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]
    raw_id_fields = ["user"]
