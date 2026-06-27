import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("availability", "0001_initial"),
        ("patients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Appointment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("confirmed", "Confirmed"),
                            ("cancelled", "Cancelled"),
                            ("completed", "Completed"),
                        ],
                        db_index=True,
                        default="confirmed",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                ("doctor_calendar_event_id", models.CharField(blank=True, default="", max_length=255)),
                ("patient_calendar_event_id", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "availability",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointment",
                        to="availability.doctoravailability",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointments",
                        to="patients.patient",
                    ),
                ),
            ],
            options={
                "verbose_name": "Appointment",
                "verbose_name_plural": "Appointments",
                "db_table": "appointments",
                "ordering": ["-created_at"],
            },
        ),
    ]
