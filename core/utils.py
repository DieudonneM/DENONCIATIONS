"""Fonctions utilitaires utilisées par les vues et dashboards."""


def check_user_can_view_incident(user, incident):
    """
    Vérifie si un utilisateur peut voir un incident.
    - Admin: peut voir tous
    - Agent: peut voir seulement de sa province
    - Travailleur: peut voir seulement les siens
    """
    if user.role == 'administrateur':
        return True
    
    if user.role == 'agent':
        # Agents can now view all incidents
        return True
    
    if user.role == 'travailleur':
        return incident.travailleur == user
    
    return False


def get_incidents_by_user_role(user):
    """
    Retourne les incidents visibles selon le rôle de l'utilisateur.
    """
    from denunciations.models import Incident
    
    if user.role == 'administrateur':
        return Incident.objects.all()
    
    if user.role == 'agent':
        # Agents can now see all incidents
        return Incident.objects.all()
    
    if user.role == 'travailleur':
        return Incident.objects.filter(travailleur=user)
    
    return Incident.objects.none()


def get_incident_statistics_by_user(user):
    """Retourne les statistiques des incidents selon le rôle de l'utilisateur."""
    incidents = get_incidents_by_user_role(user)
    
    return {
        'total': incidents.count(),
        'nouvelle': incidents.filter(statut='nouvelle').count(),
        'analyse': incidents.filter(statut='analyse').count(),
        'attente': incidents.filter(statut='attente').count(),
        'resolue': incidents.filter(statut='resolue').count(),
        'classée': incidents.filter(statut='classée').count(),
    }
