from django.contrib import admin
from availability.models import DoctorAvailability


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["doctor", "start_time", "end_time", "is_booked", "notes"]
    list_filter = ["is_booked", "doctor"]
    search_fields = ["doctor__user__email"]
    ordering = ["-start_time"]
