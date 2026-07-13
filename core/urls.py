"""
URLs pour l'application core.

Routes :
- /                              (accueil)
- /denoncier/                    (formulaire public)
- /denonciation/<code>/succes/   (page de succès)
- /consulter/                    (suivi anonyme)
- /dashboard/                    (tableau de bord)
- /incident/<code>/              (détail incident)
"""

from django.urls import path
from . import views
from . import admin_views
from denunciations import views as denunciations_views

app_name = 'core'

urlpatterns = [
    # Pages publiques
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('mot_ministre/', views.mot_ministre, name='mot_ministre'),
    path('textes_legaux/', views.textes_legaux, name='textes_legaux'),
    path('textes_legaux/<slug:slug>/', views.legal_page, name='legal_page'),
    
    # Formulaire de dénonciation (public)
    path('denoncier/', views.IncidentPublicFormView.as_view(), name='incident_form'),
    path('denonciation/<str:code>/succes/', views.IncidentSuccessView.as_view(), name='incident_success'),
    
    # Suivi anonyme
    path('consulter/', views.SearchIncidentView.as_view(), name='search_incident'),
    
    # Dashboards
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/admin/', views.DashboardAdminView.as_view(), name='dashboard_admin'),
    path('dashboard/agent/', views.DashboardAgentView.as_view(), name='dashboard_agent'),
    path('dashboard/travailleur/', views.DashboardTravailleurView.as_view(), name='dashboard_travailleur'),
    # New split dashboards
    path('dashboard/statistiques/', views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('dashboard/administration/', views.DashboardAdminConsoleView.as_view(), name='dashboard_admin_console'),
    path('dashboard/statistiques/data/', views.dashboard_stats_data, name='dashboard_stats_data'),
    
    # Détail incidents
    path('incident/<str:code>/', views.IncidentDetailView.as_view(), name='incident_detail'),
    path('incident/<str:code>/statut/', views.UpdateIncidentStatusView.as_view(), name='update_status'),
    path('incident/<str:code>/assigner/', views.AssignIncidentView.as_view(), name='assign_incident'),
    path(
        'incident/comment/<int:comment_id>/toggle-visibility/',
        denunciations_views.ToggleCommentVisibility.as_view(),
        name='toggle_comment_visibility',
    ),
    path('dashboard/incidents/', denunciations_views.IncidentsListView.as_view(), name='incidents_list'),
    path('export/incidents/xlsx/', denunciations_views.ExportIncidentsExcel.as_view(), name='export_incidents_xlsx'),
    path(
        'export/incident/<str:code>/xlsx/',
        denunciations_views.ExportIncidentExcel.as_view(),
        name='export_incident_xlsx',
    ),
    
    # ============================================================================
    #                    ADMIN PERSONNALISÉ
    # ============================================================================
    
    # Accès racine du panel admin personnalisé
    path('admin/', admin_views.admin_root, name='admin_root'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    
    # Gestion des utilisateurs
    path('admin/users/', admin_views.admin_users_list, name='admin_users_list'),
    path('admin/users/create/', admin_views.admin_users_create, name='admin_users_create'),
    path('admin/users/<int:user_id>/edit/', admin_views.admin_users_edit, name='admin_users_edit'),
    path('admin/users/<int:user_id>/delete/', admin_views.admin_users_delete, name='admin_users_delete'),
    path('admin/users/<int:user_id>/provinces/', admin_views.admin_agents_provinces, name='admin_agents_provinces'),
    
    # Gestion des provinces
    path('admin/provinces/', admin_views.admin_provinces_list, name='admin_provinces_list'),
    path('admin/provinces/create/', admin_views.admin_provinces_create, name='admin_provinces_create'),
    path('admin/provinces/<int:province_id>/edit/', admin_views.admin_provinces_edit, name='admin_provinces_edit'),
    path('admin/provinces/<int:province_id>/delete/', admin_views.admin_provinces_delete, name='admin_provinces_delete'),
    
    # Gestion des entreprises
    path('admin/employeurs/', admin_views.admin_employeurs_list, name='admin_employeurs_list'),
    path('admin/employeurs/create/', admin_views.admin_employeurs_create, name='admin_employeurs_create'),
    path('admin/employeurs/<int:employeur_id>/edit/', admin_views.admin_employeurs_edit, name='admin_employeurs_edit'),
    path('admin/employeurs/<int:employeur_id>/delete/', admin_views.admin_employeurs_delete, name='admin_employeurs_delete'),
]
