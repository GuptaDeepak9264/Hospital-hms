"""Auto-create Patient profile on user signup."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User, UserRole
from patients.models import Patient

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_patient_profile(sender, instance: User, created: bool, **kwargs):
    if created and instance.role == UserRole.PATIENT:
        Patient.objects.get_or_create(user=instance)
        logger.info("Patient profile created for user %s", instance.email)
