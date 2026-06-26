"""
URLs pour l'application denunciations.
"""

from django.urls import path
from . import views

app_name = 'denunciations'

urlpatterns = [
    # Liste des incidents (pour utilisateurs connectés)
    path('incidents/', views.IncidentsListView.as_view(), name='incidents_list'),

    # Ajout pour résoudre le NoReverseMatch dans le template incidents_list.html
    path('incident/<str:code>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    
    # Exports
    path('export/xlsx/', views.ExportIncidentsExcel.as_view(), name='export_incidents_xlsx'),
    path('export/<str:code>/xlsx/', views.ExportIncidentExcel.as_view(), name='export_incident_xlsx'),
]
