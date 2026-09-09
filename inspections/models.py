import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Entreprise(models.Model):
    """Entreprise pouvant faire l'objet d'une mission d'inspection."""

    nom = models.CharField(max_length=255)
    rccm = models.CharField(max_length=100, blank=True, db_index=True)
    nif = models.CharField(max_length=100, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Etablissement(models.Model):
    """Succursale, agence ou site d'une entreprise."""

    PROVINCE_CHOICES = (
        ('BAS_UELE', 'Bas-Uele'),
        ('EQUATEUR', 'Equateur'),
        ('HAUT_KATANGA', 'Haut-Katanga'),
        ('HAUT_LOMAMI', 'Haut-Lomami'),
        ('HAUT_UELE', 'Haut-Uele'),
        ('ITURI', 'Ituri'),
        ('KASAÏ', 'Kasaï'),
        ('KASAÏ_CENTRAL', 'Kasaï-Central'),
        ('KASAÏ_ORIENTAL', 'Kasaï-Oriental'),
        ('KINSHASA', 'Kinshasa'),
        ('KONGO_CENTRAL', 'Kongo-Central'),
        ('KWANGO', 'Kwango'),
        ('KWILU', 'Kwilu'),
        ('LOMAMI', 'Lomami'),
        ('LUALABA', 'Lualaba'),
        ('MAI_NDOMBE', 'Mai-Ndombe'),
        ('MANIEMA', 'Maniema'),
        ('MONGALA', 'Mongala'),
        ('NORD_KIVU', 'Nord-Kivu'),
        ('NORD_UBANGI', 'Nord-Ubangi'),
        ('SANKURU', 'Sankuru'),
        ('SUD_KIVU', 'Sud-Kivu'),
        ('SUD_UBANGI', 'Sud-Ubangi'),
        ('TANGANYIKA', 'Tanganyika'),
        ('TSHOPO', 'Tshopo'),
        ('TSHUAPA', 'Tshuapa'),
    )

    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='etablissements',
    )
    nom_site = models.CharField(max_length=255)
    province = models.CharField(max_length=30, choices=PROVINCE_CHOICES)
    ville_territoire = models.CharField(max_length=255)
    adresse = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Etablissement'
        verbose_name_plural = 'Etablissements'
        ordering = ['entreprise__nom', 'nom_site']

    def __str__(self):
        return f'{self.entreprise} - {self.nom_site}'


class OrdreDeMission(models.Model):
    """Ordre de mission partagé pour prévenir les inspections concurrentes."""

    ENTITE_CHOICES = (
        ('CABINET', 'Cabinet du Ministre'),
        ('IGT', 'Inspection générale du Travail'),
        ('PROVINCIALE', 'Inspection Provinciale du Travail'),
    )
    SCOPE_CHOICES = (
        ('LOCAL', 'Site spécifique'),
        ('NATIONAL', 'Siège / transversal'),
    )
    STATUT_CHOICES = (
        ('PROGRAMME', 'Programmée'),
        ('EN_COURS', 'En cours'),
        ('FINALISE', 'Finalisée'),
        ('ANNULE', 'Annulée'),
    )

    numero_om = models.CharField(max_length=50, unique=True, editable=False)
    entite_emetteure = models.CharField(max_length=20, choices=ENTITE_CHOICES)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='ordres_de_mission',
    )
    etablissement = models.ForeignKey(
        Etablissement,
        on_delete=models.CASCADE,
        related_name='ordres_de_mission',
        null=True,
        blank=True,
    )
    objet_mission = models.TextField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(
        max_length=15,
        choices=STATUT_CHOICES,
        default='PROGRAMME',
    )
    derogation_justification = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='ordres_de_mission_crees',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ordre de mission'
        verbose_name_plural = 'Ordres de mission'
        ordering = ['-date_debut', '-created_at']
        indexes = [
            models.Index(fields=['entreprise', 'scope', 'statut']),
            models.Index(fields=['etablissement', 'statut']),
            models.Index(fields=['date_debut', 'date_fin']),
        ]

    def __str__(self):
        return self.numero_om or f'Mission {self.entreprise}'

    def clean(self):
        super().clean()
        if self.scope == 'LOCAL' and not self.etablissement:
            from django.core.exceptions import ValidationError

            raise ValidationError({
                'etablissement': 'Un etablissement est obligatoire pour une mission locale.'
            })
        if self.etablissement and self.etablissement.entreprise_id != self.entreprise_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({
                'etablissement': "L'etablissement doit appartenir a l'entreprise selectionnee."
            })
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            from django.core.exceptions import ValidationError

            raise ValidationError({'date_fin': 'La date de fin doit etre posterieure a la date de debut.'})

    def check_collision(self):
        """Indique si cette mission entre en conflit avec une autre mission."""
        if not self.entreprise_id or not self.date_debut or not self.date_fin:
            return False

        missions = OrdreDeMission.objects.filter(entreprise=self.entreprise).exclude(pk=self.pk)
        same_target = Q(scope='NATIONAL')
        if self.scope == 'NATIONAL':
            same_target |= Q(scope='LOCAL')
        elif self.etablissement_id:
            same_target |= Q(scope='LOCAL', etablissement=self.etablissement)

        active_overlap = missions.filter(
            same_target,
            statut__in=('PROGRAMME', 'EN_COURS'),
            date_debut__lte=self.date_fin,
            date_fin__gte=self.date_debut,
        )
        if active_overlap.exists():
            return True

        cooling_off_start = timezone.localdate() - timedelta(days=90)
        return missions.filter(
            same_target,
            statut='FINALISE',
            date_fin__gte=cooling_off_start,
        ).exists()

    def save(self, *args, **kwargs):
        if not self.numero_om:
            self.numero_om = f'OM-{timezone.now():%Y}-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)