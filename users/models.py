"""
Modèles pour l'application users (gestion des utilisateurs).
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom User Model avec authentification par email et 3 rôles."""
    
    ROLE_CHOICES = (
        ('travailleur', 'Travailleur'),
        ('agent', 'Agent'),
        ('administrateur', 'Administrateur'),
    )
    
    # Email comme identifiant unique
    email = models.EmailField(unique=True)
    
    # Rôle utilisateur
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='travailleur')
    
    # Provinces assignées pour les agents
    provinces = models.ManyToManyField(
        'denunciations.Province',
        blank=True,
        related_name='agents',
        help_text='Provinces assignées à cet agent'
    )
    
    # Champs additionnels
    telephone = models.CharField(max_length=20, blank=True)
    organisation = models.CharField(max_length=255, blank=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    # Status du compte
    est_actif = models.BooleanField(default=True)
    # Indique que l'utilisateur doit changer son mot de passe au prochain login
    must_change_password = models.BooleanField(default=False)
    # Date/heure de création du mot de passe temporaire (si applicable)
    temp_password_set_at = models.DateTimeField(null=True, blank=True)
    
    # USERNAME_FIELD = 'email'  # Utilise email au lieu de username pour l'authentification
    # REQUIRED_FIELDS = ['username']  # username toujours requis pour createsuperuser
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_inscription']
    
    def __str__(self):
        return f'{self.get_full_name() or self.email} ({self.get_role_display()})'
    
    def get_role_display_fr(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def is_travailleur(self):
        return self.role == 'travailleur'
    
    def is_agent(self):
        return self.role == 'agent'
    
    def is_administrateur(self):
        return self.role == 'administrateur' or self.is_superuser


class UserProfile(models.Model):
    """Profil utilisateur étendu."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'
    
    def __str__(self):
        return f'Profil de {self.user.email}'
