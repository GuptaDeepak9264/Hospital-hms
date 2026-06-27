import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("doctors", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DoctorAvailability",
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
                ("start_time", models.DateTimeField(db_index=True)),
                ("end_time", models.DateTimeField()),
                ("is_booked", models.BooleanField(db_index=True, default=False)),
                ("notes", models.CharField(blank=True, default="", max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "doctor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="availability_slots",
                        to="doctors.doctor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Doctor Availability",
                "verbose_name_plural": "Doctor Availability Slots",
                "db_table": "doctor_availability",
                "ordering": ["start_time"],
            },
        ),
        migrations.AddIndex(
            model_name="doctoravailability",
            index=models.Index(
                fields=["doctor", "start_time", "end_time"],
                name="doctor_avail_doctor_start_end_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="doctoravailability",
            index=models.Index(
                fields=["doctor", "is_booked"],
                name="doctor_avail_doctor_booked_idx",
            ),
        ),
    ]
