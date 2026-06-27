import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Patient",
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
                ("date_of_birth", models.DateField(blank=True, null=True)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("male", "Male"),
                            ("female", "Female"),
                            ("other", "Other"),
                        ],
                        default="",
                        max_length=10,
                    ),
                ),
                (
                    "blood_group",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("A+", "A+"), ("A-", "A-"),
                            ("B+", "B+"), ("B-", "B-"),
                            ("AB+", "AB+"), ("AB-", "AB-"),
                            ("O+", "O+"), ("O-", "O-"),
                        ],
                        default="",
                        max_length=5,
                    ),
                ),
                ("phone", models.CharField(blank=True, default="", max_length=20)),
                ("address", models.TextField(blank=True, default="")),
                ("medical_history", models.TextField(blank=True, default="")),
                (
                    "google_calendar_token_path",
                    models.CharField(blank=True, default="", max_length=500),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "patient"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patient_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Patient",
                "verbose_name_plural": "Patients",
                "db_table": "patients",
            },
        ),
    ]
