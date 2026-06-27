"""
Django signals for the doctors app.
Automatically creates a Doctor profile whenever a User with role='doctor' is saved.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User, UserRole
from doctors.models import Doctor

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_doctor_profile(sender, instance: User, created: bool, **kwargs):
    """Create a Doctor profile row when a new doctor user is registered."""
    if created and instance.role == UserRole.DOCTOR:
        Doctor.objects.get_or_create(user=instance)
        logger.info("Doctor profile created for user %s", instance.email)
