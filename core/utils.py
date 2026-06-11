"""
Fonctions utilitaires pour l'application.
"""

import os
from django.core.files.storage import default_storage
from django.conf import settings


def get_file_size(file_obj):
    """Retourne la taille du fichier en bytes."""
    if hasattr(file_obj, 'size'):
        return file_obj.size
    elif hasattr(file_obj, '_size'):
        return file_obj._size
    return 0


def get_file_extension(filename):
    """Retourne l'extension du fichier."""
    return os.path.splitext(filename)[1].lower().lstrip('.')


def format_file_size(size_bytes):
    """Formate la taille du fichier en format lisible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f'{size_bytes:.2f} {unit}'
        size_bytes /= 1024.0
    return f'{size_bytes:.2f} TB'


def get_file_type_from_extension(extension):
    """Retourne le type de fichier basé sur l'extension."""
    extension = extension.lower()
    
    type_mapping = {
        'pdf': 'PDF',
        'doc': 'DOC',
        'docx': 'DOCX',
        'jpg': 'IMAGE',
        'jpeg': 'IMAGE',
        'png': 'IMAGE',
        'gif': 'IMAGE',
        'mp4': 'VIDEO',
        'mp3': 'AUDIO',
        'wav': 'AUDIO',
    }
    
    return type_mapping.get(extension, 'AUTRE')


def generate_tracking_code():
    """Génère un code de suivi unique."""
    from django.utils import timezone
    from denunciations.models import Incident
    import uuid
    
    unique_part = str(uuid.uuid4())[:8].upper()
    year = timezone.now().year
    return f'RDC{year}{unique_part}'


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
        if incident.province in user.provinces.all():
            return True
    
    if user.role == 'travailleur':
        if incident.travailleur == user:
            return True
    
    return False


def get_incidents_by_user_role(user):
    """
    Retourne les incidents visibles selon le rôle de l'utilisateur.
    """
    from denunciations.models import Incident
    
    if user.role == 'administrateur':
        return Incident.objects.all()
    
    if user.role == 'agent':
        return Incident.objects.filter(province__in=user.provinces.all())
    
    if user.role == 'travailleur':
        return Incident.objects.filter(travailleur=user)
    
    return Incident.objects.none()


def get_incident_statistics_by_user(user):
    """
    Retourne les statistiques des incidents selon le rôle de l'utilisateur.
    """
    from denunciations.models import Incident
    from django.db.models import Q, Count
    
    incidents = get_incidents_by_user_role(user)
    
    return {
        'total': incidents.count(),
        'nouvelle': incidents.filter(statut='nouvelle').count(),
        'analyse': incidents.filter(statut='analyse').count(),
        'attente': incidents.filter(statut='attente').count(),
        'resolue': incidents.filter(statut='resolue').count(),
        'classée': incidents.filter(statut='classée').count(),
    }
