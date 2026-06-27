from django.contrib import admin
from appointments.models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["id", "patient", "get_doctor", "get_slot_time", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["patient__user__email", "availability__doctor__user__email"]
    ordering = ["-created_at"]

    def get_doctor(self, obj):
        return obj.availability.doctor.user.get_full_name()
    get_doctor.short_description = "Doctor"

    def get_slot_time(self, obj):
        return obj.availability.start_time.strftime("%Y-%m-%d %H:%M")
    get_slot_time.short_description = "Slot Time"
