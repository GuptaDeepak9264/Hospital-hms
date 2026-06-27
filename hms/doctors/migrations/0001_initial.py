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
            name="Doctor",
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
                ("specialization", models.CharField(blank=True, default="", max_length=200)),
                ("qualification", models.CharField(blank=True, default="", max_length=300)),
                ("experience_years", models.PositiveIntegerField(default=0)),
                (
                    "consultation_fee",
                    models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
                ),
                ("bio", models.TextField(blank=True, default="")),
                (
                    "google_calendar_token_path",
                    models.CharField(blank=True, default="", max_length=500),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        limit_choices_to={"role": "doctor"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="doctor_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Doctor",
                "verbose_name_plural": "Doctors",
                "db_table": "doctors",
            },
        ),
    ]
