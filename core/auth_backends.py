"""
Configuration d'authentification et permissions personnalisées.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserBackend(ModelBackend):
    """
    Authentification personnalisée pour supporter les rôles d'utilisateurs.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie l'utilisateur avec vérification du rôle.
        """
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and user.is_active:
            return user
        
        return None
    
    def get_user(self, user_id):
        """Récupère l'utilisateur par ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def user_is_travailleur(user):
    """Vérifie si l'utilisateur est un travailleur."""
    return bool(getattr(user, 'is_authenticated', False) and getattr(user, 'role', None) == 'travailleur')


def user_is_agent(user):
    """Vérifie si l'utilisateur est un agent."""
    return bool(getattr(user, 'is_authenticated', False) and getattr(user, 'role', None) == 'agent')


def user_is_admin(user):
    """Vérifie si l'utilisateur est administrateur."""
    return bool(
        getattr(user, 'is_authenticated', False)
        and (getattr(user, 'role', None) == 'administrateur' or getattr(user, 'is_superuser', False))
    )


def user_is_staff(user):
    """Vérifie si l'utilisateur est du personnel (agent ou admin)."""
    return bool(getattr(user, 'is_authenticated', False) and getattr(user, 'role', None) in ['agent', 'administrateur'])
