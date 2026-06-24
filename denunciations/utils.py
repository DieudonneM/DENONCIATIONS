"""
Fonctions utilitaires pour l'application denunciations.
"""

import os
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


def check_user_can_view_incident(user, incident):
    """
    Vérifie si un utilisateur peut voir un incident.
    - Admin: peut voir tous
    - Agent: peut voir seulement de sa province
    - Travailleur: peut voir seulement les siens
    """
    from users.auth_backends import user_is_agent, user_is_admin
    
    if user_is_admin(user):
        return True
    
    if user_is_agent(user):
        # Agents can view all incidents
        return True
    
    if user.role == 'travailleur':
        if incident.travailleur == user:
            return True
    
    return False


def get_incidents_by_user_role(user):
    """
    Retourne les incidents visibles selon le rôle de l'utilisateur.
    """
    from .models import Incident
    from users.auth_backends import user_is_agent, user_is_admin
    
    if user_is_admin(user):
        return Incident.objects.all()
    
    if user_is_agent(user):
        # Agents can now see all incidents
        return Incident.objects.all()
    
    if user.role == 'travailleur':
        return Incident.objects.filter(travailleur=user)
    
    return Incident.objects.none()
