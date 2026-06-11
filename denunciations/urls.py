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
    
    # Détails (nécessite authentification)
    path('detail/<str:code>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    path('detail/<str:code>/statut/', views.UpdateIncidentStatusView.as_view(), name='update_status'),
    path('detail/<str:code>/assigner/', views.AssignIncidentView.as_view(), name='assign_incident'),
]
