"""
Signals pour l'application users (profil utilisateur, etc.)
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Créer ou mettre à jour le profil utilisateur."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        try:
            instance.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)
