"""
Authentification personnalisée pour l'application.
"""

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone
from users.models import User
from users.services import TEMPORARY_PASSWORD_TTL


class EmailBackend(ModelBackend):
    """Backend d'authentification par email."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifier par email ou username.
        """
        try:
            # Essayer d'abord par email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Sinon essayer par username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        
        if not user.check_password(password) or not user.is_active:
            return None

        if user.must_change_password:
            set_at = user.temp_password_set_at
            if (
                set_at is None
                or timezone.now() - set_at > TEMPORARY_PASSWORD_TTL
                or user.temp_password_used_at is not None
            ):
                return None

            used_at = timezone.now()
            consumed = User.objects.filter(
                pk=user.pk,
                temp_password_used_at__isnull=True,
            ).update(temp_password_used_at=used_at)
            if not consumed:
                return None
            user.temp_password_used_at = used_at

        return user
        
    def get_user(self, user_id):
        """Récupérer l'utilisateur par ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# Fonctions utilitaires pour vérifier les rôles
def user_is_travailleur(user):
    """Vérifier si l'utilisateur est un travailleur."""
    return user and hasattr(user, 'role') and user.role == 'travailleur'


def user_is_agent(user):
    """Vérifier si l'utilisateur est un agent."""
    return user and hasattr(user, 'role') and user.role == 'agent'


def user_is_admin(user):
    """Vérifier si l'utilisateur est administrateur."""
    return user and (
        (hasattr(user, 'role') and user.role == 'administrateur') or 
        user.is_superuser
    )


def user_is_staff(user):
    """Vérifier si l'utilisateur est du personnel."""
    return user and (user_is_agent(user) or user_is_admin(user))
