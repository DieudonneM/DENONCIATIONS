"""
Configuration Admin Django pour l'application core.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from .models import Province, Employeur


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'nombre_incidents', 'nombre_agents']
    list_filter = ['date_creation']
    search_fields = ['nom', 'code']
    ordering = ['nom']
    
    def nombre_incidents(self, obj):
        count = obj.incidents.count()
        return count or '-'
    nombre_incidents.short_description = 'Incidents'
    
    def nombre_agents(self, obj):
        count = obj.agents.count()
        return count or '-'
    nombre_agents.short_description = 'Agents assignés'


@admin.register(Employeur)
class EmployeurAdmin(admin.ModelAdmin):
    list_display = ['nom', 'secteur', 'province', 'ville', 'nombre_incidents', 'date_creation']
    list_filter = ['secteur', 'province', 'date_creation']
    search_fields = ['nom', 'email', 'telephone', 'ville']
    readonly_fields = ['date_creation', 'date_modification', 'nombre_incidents']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'secteur', 'description')
        }),
        ('Localisation', {
            'fields': ('province', 'ville')
        }),
        ('Contact', {
            'fields': ('email', 'telephone')
        }),
        ('Historique', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_incidents(self, obj):
        return obj.incidents.count()
    nombre_incidents.short_description = 'Nombre d\'incidents'


# Customization de l'admin site
admin.site.site_header = "Administration - Plateforme de Dénonciation des Incidents de Travail"
admin.site.site_title = "Admin MEPT-RDC"
admin.site.index_title = "Tableau de bord administrateur"
