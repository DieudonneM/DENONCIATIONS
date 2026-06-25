"""
URLs pour l'application denunciations.
"""

from django.urls import path
from . import views

app_name = 'denunciations'

urlpatterns = [
    # Dénonciation publique
    path('denonciation/', views.IncidentPublicFormView.as_view(), name='incident_form'),
    path('denonciation/succes/<str:code>/', views.IncidentSuccessView.as_view(), name='incident_success'),
    path('rechercher/', views.SearchIncidentView.as_view(), name='search_incident'),
    path('incidents/', views.IncidentsListView.as_view(), name='incidents_list'),
    
    # Détails (nécessite authentification)
    path('detail/<str:code>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    path('detail/<str:code>/statut/', views.UpdateIncidentStatusView.as_view(), name='update_status'),
    path('detail/<str:code>/assigner/', views.AssignIncidentView.as_view(), name='assign_incident'),
    path('detail/comment/<int:comment_id>/toggle_visibility/', views.ToggleCommentVisibility.as_view(), name='toggle_comment_visibility'),
    path('export/xlsx/', views.ExportIncidentsExcel.as_view(), name='export_incidents_xlsx'),
    path('export/<str:code>/xlsx/', views.ExportIncidentExcel.as_view(), name='export_incident_xlsx'),
]
