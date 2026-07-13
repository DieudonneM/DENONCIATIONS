"""
Modèles pour l'application core (Province et Employeur).
Les modèles de dénonciation (Incident, Commentaire, etc.) sont dans denunciations.models
"""

import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from django.conf import settings


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
    adresse_complete = models.TextField(blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Employeur'
        verbose_name_plural = 'Employeurs'
        ordering = ['nom']
        unique_together = ('nom', 'province')
    
    def __str__(self):
        return self.nom


class Department(models.Model):
    """Département interne pouvant recevoir des dénonciations par email."""

    nom = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    utilisateurs = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='departments',
        help_text='Utilisateurs appartenant à ce département'
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['nom']

    def __str__(self):
        return self.nom
