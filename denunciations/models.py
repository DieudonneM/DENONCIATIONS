"""
Modèles pour l'application denunciations (gestion des dénonciations).
"""

import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from users.models import User


class Province(models.Model):
    """Modèle représentant une province de la RDC."""
    
    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Province'
        verbose_name_plural = 'Provinces'
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Employeur(models.Model):
    """Modèle représentant un employeur/entreprise."""
    
    SECTEUR_CHOICES = (
        ('agriculture', 'Agriculture'),
        ('industrie', 'Industrie'),
        ('commerce', 'Commerce'),
        ('services', 'Services'),
        ('sante', 'Santé'),
        ('education', 'Éducation'),
        ('energie', 'Énergie'),
        ('mines', 'Mines'),
        ('construction', 'Construction'),
        ('transport', 'Transport'),
        ('telecommunications', 'Télécommunications'),
        ('finance', 'Finance'),
        ('administration', 'Administration Publique'),
        ('autre', 'Autre'),
    )
    
    nom = models.CharField(max_length=255)
    secteur = models.CharField(max_length=50, choices=SECTEUR_CHOICES)
    description = models.TextField(blank=True)
    
    # Localisation
    ville = models.CharField(max_length=100, blank=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employeurs'
    )
    
    # Contact
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Employeur'
        verbose_name_plural = 'Employeurs'
        ordering = ['nom']
        unique_together = ('nom', 'province')
    
    def __str__(self):
        return self.nom


class Incident(models.Model):
    """Modèle représentant une dénonciation/incident de travail."""
    
    TYPE_INCIDENT_CHOICES = (
        ('salaire', 'Non-paiement du salaire'),
        ('horaires', 'Horaires excessifs'),
        ('securite', 'Conditions de sécurité insuffisantes'),
        ('discrimination', 'Discrimination'),
        ('harcèlement', 'Harcèlement'),
        ('travail_enfant', 'Travail des enfants'),
        ('travail_force', 'Travail forcé'),
        ('congé', 'Refus de congé'),
        ('cotisations', 'Non-versement des cotisations sociales'),
        ('licenciement', 'Licenciement abusif'),
        ('autre', 'Autre'),
    )
    
    STATUT_CHOICES = (
        ('nouvelle', 'Nouvelle'),
        ('analyse', 'En cours d\'analyse'),
        ('attente', 'En attente d\'informations'),
        ('resolue', 'Résolue'),
        ('classée', 'Classée sans suite'),
    )
    
    # Code de suivi unique
    code_suivi = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        db_index=True
    )
    
    # Relation avec le travailleur (optionnelle pour anonymat)
    travailleur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        limit_choices_to={'role': 'travailleur'}
    )
    
    # Relation avec l'employeur
    employeur = models.ForeignKey(
        Employeur,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    
    # Localisation
    ville = models.CharField(max_length=100)
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents'
    )
    
    # Détails de l'incident
    type_incident = models.CharField(
        max_length=50,
        choices=TYPE_INCIDENT_CHOICES
    )
    # Si l'utilisateur choisit 'autre', on conserve le texte précisé ici
    type_incident_autre = models.CharField(max_length=255, blank=True)
    # Champ libre pour indiquer le fautif (nom ou description)
    le_fautif = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    
    # Statut et gestion
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='nouvelle',
        db_index=True
    )
    
    # Agent assigné
    agent_assigné = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents_assignés',
        limit_choices_to={'role': 'agent'}
    )
    
    # Informations anonyme
    est_anonyme = models.BooleanField(default=True)
    email_contact_anonyme = models.EmailField(blank=True)
    telephone_contact_anonyme = models.CharField(max_length=20, blank=True)
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    # Marquer comme "lu" pour la notification
    est_lu = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['code_suivi']),
            models.Index(fields=['statut', '-date_creation']),
            models.Index(fields=['province', 'statut']),
        ]
    
    def get_default_agent_for_province(self):
        """Retourne le premier agent disponible pour la province de l'incident."""
        if not self.province:
            return None
        return User.objects.filter(
            role='agent',
            is_active=True,
            provinces=self.province
        ).order_by('date_inscription', 'id').first()

    def save(self, *args, **kwargs):
        """Générer un code de suivi unique et assigner un agent par province à la création."""
        if not self.code_suivi:
            # Format : RDC + Année + UUID court
            unique_part = str(uuid.uuid4())[:8].upper()
            year = timezone.now().year
            self.code_suivi = f'RDC{year}{unique_part}'

        creating = self.pk is None
        super().save(*args, **kwargs)

        # Assigner automatiquement un agent disponible de la province à la création,
        # seulement si aucun agent n'a été explicitement défini.
        if creating and not self.agent_assigné and self.province:
            default_agent = self.get_default_agent_for_province()
            if default_agent:
                self.agent_assigné = default_agent
                models.Model.save(self, update_fields=['agent_assigné'])

    def __str__(self):
        return f'{self.code_suivi} - {self.get_type_incident_display()}'

    def get_type_incident_display(self):
        """Retourne l'affichage lisible du type d'incident, en gérant le cas 'autre'."""
        if self.type_incident == 'autre' and self.type_incident_autre:
            return f'Autre - {self.type_incident_autre}'
        mapping = dict(self.TYPE_INCIDENT_CHOICES)
        return mapping.get(self.type_incident, self.type_incident)


class PieceJointe(models.Model):
    """Modèle pour les pièces jointes liées aux incidents."""
    
    EXTENSIONS_AUTORISEES = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mp3', 'wav']
    
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='pieces_jointes'
    )
    
    fichier = models.FileField(
        upload_to='incidents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=EXTENSIONS_AUTORISEES)]
    )
    
    nom_original = models.CharField(max_length=255)
    type_fichier = models.CharField(max_length=50)
    taille_fichier = models.BigIntegerField()  # en bytes
    
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pièce Jointe'
        verbose_name_plural = 'Pièces Jointes'
        ordering = ['-date_ajout']
    
    def __str__(self):
        return f'{self.nom_original} - {self.incident.code_suivi}'


class Commentaire(models.Model):
    """Modèle pour les commentaires/communications liées aux incidents."""
    
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='commentaires'
    )
    
    auteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commentaires'
    )
    
    texte = models.TextField()
    
    # Typage du commentaire
    EST_INTERNE = 'interne'
    EST_PUBLIC = 'public'
    TYPE_CHOICES = (
        (EST_INTERNE, 'Interne (Agents uniquement)'),
        (EST_PUBLIC, 'Public (Visible au travailleur)'),
    )
    type_commentaire = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=EST_INTERNE
    )
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['-date_creation']
    
    def __str__(self):
        return f'Commentaire sur {self.incident.code_suivi} par {self.auteur}'


class LogAudit(models.Model):
    """Modèle pour tracker les modifications importantes."""
    
    ACTION_CHOICES = (
        ('creation', 'Création'),
        ('modification_statut', 'Modification de statut'),
        ('assignation', 'Assignation d\'agent'),
        ('ajout_commentaire', 'Ajout commentaire'),
        ('ajout_piece', 'Ajout pièce jointe'),
        ('resolution', 'Résolution'),
    )
    
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_audit'
    )
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ancienne_valeur = models.TextField(blank=True)
    nouvelle_valeur = models.TextField(blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Log d\'Audit'
        verbose_name_plural = 'Logs d\'Audit'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['incident', '-date_creation']),
        ]
    
    def __str__(self):
        return f'{self.action} - {self.incident.code_suivi}'
