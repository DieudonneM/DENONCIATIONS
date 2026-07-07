"""
Admin pour l'application denunciations.
"""

from django.contrib import admin
from .models import Province, Employeur, Incident, PieceJointe, Commentaire, LogAudit


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'date_creation']
    search_fields = ['nom', 'code']
    readonly_fields = ['date_creation']


@admin.register(Employeur)
class EmployeurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'secteur', 'province', 'adresse_complete', 'date_creation']
    list_filter = ['secteur', 'province', 'date_creation']
    search_fields = ['nom', 'email', 'telephone']
    readonly_fields = ['date_creation', 'date_modification']
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'secteur', 'description', 'adresse_complete')
        }),
        ('Localisation', {
            'fields': ('ville', 'province')
        }),
        ('Contact', {
            'fields': ('email', 'telephone')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ['code_suivi', 'type_incident', 'statut', 'employeur', 'employeur_secteur', 'accepted_privacy', 'accepted_privacy_at', 'date_creation']
    list_filter = ['statut', 'type_incident', 'province', 'est_anonyme', 'accepted_privacy', 'date_creation']
    search_fields = ['code_suivi', 'employeur__nom', 'description']
    readonly_fields = ['code_suivi', 'date_creation', 'date_modification']
    fieldsets = (
        ('Code de suivi', {
            'fields': ('code_suivi',)
        }),
        ('Travailleur', {
            'fields': ('travailleur', 'est_anonyme')
        }),
        ('Incident', {
            'fields': ('type_incident', 'employeur', 'province', 'ville', 'description')
        }),
        ('Statut et assignation', {
            'fields': ('statut', 'agent_assigné', 'date_resolution')
        }),
        ('Contact anonyme', {
            'fields': ('email_contact_anonyme', 'telephone_contact_anonyme'),
            'classes': ('collapse',)
        }),
        ('Preuve d\'acceptation', {
            'fields': ('accepted_privacy', 'accepted_privacy_at'),
            'classes': ('collapse',)
        }),
        ('Suivi', {
            'fields': ('est_lu', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ['travailleur', 'employeur', 'type_incident']
        return self.readonly_fields

    def employeur_secteur(self, obj):
        if obj.employeur:
            return obj.employeur.secteur
        return ''
    employeur_secteur.short_description = 'Secteur Employeur'


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['incident', 'auteur', 'type_commentaire', 'date_creation']
    list_filter = ['type_commentaire', 'date_creation']
    search_fields = ['incident__code_suivi', 'auteur__email', 'texte']
    readonly_fields = ['date_creation', 'date_modification']


@admin.register(PieceJointe)
class PieceJointeAdmin(admin.ModelAdmin):
    list_display = ['nom_original', 'incident', 'type_fichier', 'taille_fichier', 'date_ajout']
    list_filter = ['type_fichier', 'date_ajout']
    search_fields = ['nom_original', 'incident__code_suivi']
    readonly_fields = ['date_ajout']


@admin.register(LogAudit)
class LogAuditAdmin(admin.ModelAdmin):
    list_display = ['incident', 'action', 'utilisateur', 'date_creation']
    list_filter = ['action', 'date_creation']
    search_fields = ['incident__code_suivi', 'utilisateur__email', 'description']
    readonly_fields = ['date_creation', 'incident', 'action', 'utilisateur', 'description', 'ancienne_valeur', 'nouvelle_valeur']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
