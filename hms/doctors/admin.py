from django.contrib import admin
from doctors.models import Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["user", "specialization", "experience_years", "consultation_fee"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "specialization"]
    raw_id_fields = ["user"]
