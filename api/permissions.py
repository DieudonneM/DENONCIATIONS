from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Permet l'accès complet aux administrateurs."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (getattr(user, 'is_administrateur', lambda: False)() if callable(getattr(user, 'is_administrateur', None)) else (user.is_superuser or getattr(user, 'role', '') == 'administrateur')))

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAgent(BasePermission):
    """Permet aux agents de lire/modifier toutes les dénonciations et commentaires."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (callable(getattr(user, 'is_agent', None)) and user.is_agent()))

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwnerTravailleur(BasePermission):
    """Permet au travailleur d'agir uniquement sur ses propres dénonciations/commentaires."""

    def has_permission(self, request, view):
        # For list/create we'll allow authenticated travailleurs to proceed; object-level checks happen in has_object_permission
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, 'role', '') == 'travailleur')

    def has_object_permission(self, request, view, obj):
        # obj expected to have attribute `travailleur` or `incident`
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if getattr(user, 'role', '') != 'travailleur':
            return False
        # If object is an incident
        if hasattr(obj, 'travailleur'):
            return obj.travailleur == user
        # If object is a comment
        if hasattr(obj, 'incident'):
            return getattr(obj.incident, 'travailleur', None) == user
        return False


class IsAdminAgentOrOwner(BasePermission):
    """Composite permission: admin OR agent OR owner(travailleur).

    Use this as the primary permission on viewsets where these roles are allowed.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # Admin
        if (callable(getattr(user, 'is_administrateur', None)) and user.is_administrateur()) or user.is_superuser or getattr(user, 'role', '') == 'administrateur':
            return True
        # Agent
        if callable(getattr(user, 'is_agent', None)) and user.is_agent():
            return True
        # Travailleur can list/create but object-level enforced separately
        if getattr(user, 'role', '') == 'travailleur':
            return True
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # Admin
        if (callable(getattr(user, 'is_administrateur', None)) and user.is_administrateur()) or user.is_superuser or getattr(user, 'role', '') == 'administrateur':
            return True
        # Agent
        if callable(getattr(user, 'is_agent', None)) and user.is_agent():
            return True
        # Owner (travailleur)
        if getattr(user, 'role', '') == 'travailleur':
            if hasattr(obj, 'travailleur'):
                return obj.travailleur == user
            if hasattr(obj, 'incident'):
                return getattr(obj.incident, 'travailleur', None) == user
        return False
