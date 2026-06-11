"""
Admin pour l'application users.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour le modèle User."""
    
    list_display = ['email', 'get_full_name', 'role', 'is_active', 'date_inscription']
    list_filter = ['role', 'is_active', 'date_inscription']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    
    fieldsets = (
        ('Informations d\'authentification', {
            'fields': ('username', 'email', 'password')
        }),
        ('Profil', {
            'fields': ('first_name', 'last_name', 'telephone', 'organisation')
        }),
        ('Rôle et permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Provinces assignées', {
            'fields': ('provinces',),
            'classes': ('collapse',),
            'description': 'Applicable uniquement pour les agents'
        }),
        ('Dates', {
            'fields': ('date_inscription', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Profil', {
            'fields': ('first_name', 'last_name', 'role', 'telephone', 'organisation')
        }),
    )
    
    readonly_fields = ['date_inscription', 'last_login']
    ordering = ['-date_inscription']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin pour les profils utilisateurs étendus."""
    
    list_display = ['user', 'date_mise_a_jour']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['date_mise_a_jour']
