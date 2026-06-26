from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Incident, Commentaire

@receiver(pre_save, sender=Incident)
def store_old_incident_status(sender, instance, **kwargs):
    """
    Avant de sauvegarder un incident, stocke son ancien statut
    pour le comparer après la sauvegarde.
    """
    if instance.pk:
        try:
            previous = Incident.objects.get(pk=instance.pk)
            instance._old_status_display = previous.get_statut_display()
            instance._old_status_value = previous.statut
        except Incident.DoesNotExist:
            # L'objet n'existe pas encore dans la base de données
            pass

@receiver(post_save, sender=Incident)
def notify_user_on_status_change(sender, instance, created, **kwargs):
    """
    Envoie une notification par e-mail au travailleur lorsque le statut
    d'un incident est modifié.
    """
    if created:
        return

    old_status_value = getattr(instance, '_old_status_value', None)
    if old_status_value is None or old_status_value == instance.statut:
        return

    if not instance.est_anonyme and instance.travailleur and instance.travailleur.email:
        subject = f"Mise à jour de votre dénonciation : {instance.code_suivi}"
        
        context = {
            'user_name': instance.travailleur.get_full_name() or instance.travailleur.email,
            'incident_code': instance.code_suivi,
            'old_status': getattr(instance, '_old_status_display', 'N/A'),
            'new_status': instance.get_statut_display(),
            'change_type': 'status_update',
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        }

        html_message = render_to_string('denunciations/emails/notification_body.html', context)
        plain_message = render_to_string('denunciations/emails/notification_body.txt', context)

        send_mail(
            subject,
            plain_message,
            f"MINISTERE DE L'EMPLOI ET TRAVAIL <{settings.DEFAULT_FROM_EMAIL}>",
            [instance.travailleur.email],
            html_message=html_message,
            fail_silently=False,
        )

@receiver(post_save, sender=Commentaire)
def notify_user_on_new_public_comment(sender, instance, created, **kwargs):
    """
    Envoie une notification par e-mail au travailleur lorsqu'un nouveau
    commentaire public est ajouté à son incident.
    """
    if not created or instance.type_commentaire != 'public':
        return

    incident = instance.incident
    if not incident.est_anonyme and incident.travailleur and incident.travailleur.email:
        subject = f"Nouveau commentaire sur votre dénonciation : {incident.code_suivi}"
        
        context = {
            'user_name': incident.travailleur.get_full_name() or incident.travailleur.email,
            'incident_code': incident.code_suivi,
            'comment_author': instance.auteur.get_full_name(),
            'comment_text': instance.texte,
            'change_type': 'new_comment',
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
        }

        html_message = render_to_string('denunciations/emails/notification_body.html', context)
        plain_message = render_to_string('denunciations/emails/notification_body.txt', context)

        send_mail(
            subject,
            plain_message,
            f"MINISTERE DE L'EMPLOI ET TRAVAIL <{settings.DEFAULT_FROM_EMAIL}>",
            [incident.travailleur.email],
            html_message=html_message,
            fail_silently=False,
        )