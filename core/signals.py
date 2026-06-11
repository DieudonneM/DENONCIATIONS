"""
Signaux Django pour les opérations automatiques.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from denunciations.models import Incident, Commentaire, LogAudit
from django.utils import timezone


@receiver(post_save, sender=Incident)
def incident_created(sender, instance, created, **kwargs):
    """
    Appelé après la création/modification d'un incident.
    Crée automatiquement un log d'audit.
    """
    if created:
        LogAudit.objects.create(
            incident=instance,
            utilisateur=None,
            action='creation',
            description=f'Incident créé : {instance.code_suivi}'
        )


@receiver(pre_save, sender=Incident)
def incident_status_changed(sender, instance, **kwargs):
    """
    Vérifie si le statut de l'incident a changé.
    Si oui, crée un log d'audit et met à jour la date de résolution.
    """
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    
    # Vérifier si le statut a changé
    if old_instance.statut != instance.statut:
        LogAudit.objects.create(
            incident=instance,
            action='modification_statut',
            description=f'Statut changé de {old_instance.get_statut_display()} à {instance.get_statut_display()}',
            ancienne_valeur=old_instance.statut,
            nouvelle_valeur=instance.statut
        )
        
        # Si résolu, mettre à jour la date de résolution
        if instance.statut == 'resolue' and not instance.date_resolution:
            instance.date_resolution = timezone.now()
    
    # Vérifier si un agent a été assigné
    if old_instance.agent_assigné != instance.agent_assigné:
        if instance.agent_assigné:
            LogAudit.objects.create(
                incident=instance,
                utilisateur=instance.agent_assigné,
                action='assignation',
                description=f'Assigné à {instance.agent_assigné.get_full_name()}',
                nouvelle_valeur=instance.agent_assigné.username
            )


@receiver(post_save, sender=Commentaire)
def commentaire_created(sender, instance, created, **kwargs):
    """
    Appelé après la création d'un commentaire.
    Crée un log d'audit.
    """
    if created:
        LogAudit.objects.create(
            incident=instance.incident,
            utilisateur=instance.auteur,
            action='ajout_commentaire',
            description=f'Commentaire ajouté ({instance.get_type_commentaire_display()})',
            nouvelle_valeur=instance.texte[:100]
        )
