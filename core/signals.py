"""
Signaux Django pour les opérations automatiques.
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.db import transaction
from django.dispatch import receiver
from denunciations.models import Incident, Commentaire, LogAudit
from django.utils import timezone

from .push_notifications import send_incident_comment_push, send_incident_status_change_push


logger = logging.getLogger(__name__)


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
        # Mémorisé pour l'envoi push en post_save (après commit).
        instance._old_status_for_push = old_instance.statut

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

    # Vérifier si un département a été assigné
    if getattr(old_instance, 'department_assigné', None) != getattr(instance, 'department_assigné', None):
        if getattr(instance, 'department_assigné', None):
            dept = instance.department_assigné
            LogAudit.objects.create(
                incident=instance,
                utilisateur=None,
                action='assignation_departement',
                description=f'Assigné au département {dept.nom}',
                nouvelle_valeur=dept.nom
            )


@receiver(post_save, sender=Incident)
def incident_status_push_notification(sender, instance, created, **kwargs):
    """Envoi push lorsque le statut d'un incident change."""
    if created:
        return

    old_status = getattr(instance, '_old_status_for_push', None)
    if not old_status or old_status == instance.statut:
        return

    def _send():
        try:
            result = send_incident_status_change_push(
                incident=instance,
                old_status=old_status,
                new_status=instance.statut,
            )
            logger.info(
                'Push statut incident=%s old=%s new=%s result=%s',
                instance.code_suivi,
                old_status,
                instance.statut,
                result,
            )
        except Exception:
            logger.exception('Erreur envoi push statut incident=%s', instance.code_suivi)

    transaction.on_commit(_send)

@receiver(post_save, sender=Commentaire)
def commentaire_created(sender, instance, created, **kwargs):
    """
    Appelé après la création d'un commentaire.
    Crée un log d'audit et envoie une notification push si le commentaire est public et émis par le ministère.
    """
    if created:
        LogAudit.objects.create(
            incident=instance.incident,
            utilisateur=instance.auteur,
            action='ajout_commentaire',
            description=f'Commentaire ajouté ({instance.get_type_commentaire_display()})',
            nouvelle_valeur=instance.texte[:100]
        )

        if (
            instance.type_commentaire == Commentaire.EST_PUBLIC
            and instance.origine_public == Commentaire.ORIGINE_MINISTERE
        ):
            def _send_comment_push():
                try:
                    result = send_incident_comment_push(
                        incident=instance.incident,
                        commentaire=instance,
                    )
                    logger.info(
                        'Push commentaire incident=%s result=%s',
                        instance.incident.code_suivi,
                        result,
                    )
                except Exception:
                    logger.exception(
                        'Erreur envoi push commentaire incident=%s',
                        instance.incident.code_suivi,
                    )

            transaction.on_commit(_send_comment_push)
