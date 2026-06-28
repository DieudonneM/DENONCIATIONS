"""
URLs pour l'application core.

Routes gérées ici : pages statiques, dashboards, panel admin personnalisé et URLs publiques des dénonciations.
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
    
    # Formulaire de dénonciation (public) - pointe vers denunciations.views
    path('denoncier/', denunciations_views.IncidentPublicFormView.as_view(), name='incident_form'),
    path('denonciation/<str:code>/succes/', denunciations_views.IncidentSuccessView.as_view(), name='incident_success'),
    
    # Suivi anonyme - pointe vers denunciations.views
    path('consulter/', denunciations_views.SearchIncidentView.as_view(), name='search_incident'),
    
    # Dashboards
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/agent/', views.DashboardAgentView.as_view(), name='dashboard_agent'),
    path('dashboard/travailleur/', views.DashboardTravailleurView.as_view(), name='dashboard_travailleur'),

    # Détail et modification des incidents (pour la cohérence des URLs)
    path('incident/<str:code>/', denunciations_views.IncidentDetailView.as_view(), name='incident_detail'),
    path('incident/<str:code>/modifier/', views.EditIncidentView.as_view(), name='incident_edit'),
    path('incident/<str:code>/statut/', denunciations_views.UpdateIncidentStatusView.as_view(), name='update_status'),
    path('incident/<str:code>/assigner/', denunciations_views.AssignIncidentView.as_view(), name='assign_incident'),
    path('commentaire/<int:comment_id>/toggle_visibility/', denunciations_views.ToggleCommentVisibility.as_view(), name='toggle_comment_visibility'),
    
    # ============================================================================
    #                    ADMIN PERSONNALISÉ
    # ============================================================================
    
    # Accès racine du panel admin personnalisé
    path('admin/', admin_views.admin_root, name='admin_root'),
    path('admin/dashboard/', admin_views.admin_statistics_dashboard, name='admin_dashboard'),
    path('admin/dashboard/chart/<str:chart_type>/', admin_views.admin_chart_detail, name='admin_chart_detail'),
    path('admin/management/', admin_views.admin_global_management, name='admin_global_management'),
    
    # Gestion des utilisateurs
    path('admin/users/', admin_views.admin_users_list, name='admin_users_list'),
    path('admin/users/create/', admin_views.admin_users_create, name='admin_users_create'),
    path('admin/users/<int:user_id>/edit/', admin_views.admin_users_edit, name='admin_users_edit'),
    path('admin/users/<int:user_id>/delete/', admin_views.admin_users_delete, name='admin_users_delete'),
    path('admin/users/<int:user_id>/send-reset-link/', admin_views.admin_users_send_reset_link, name='admin_users_send_reset_link'), # Nouvelle URL
    # Alias pour la rétrocompatibilité avec les templates qui utilisent encore les anciens noms d'URL
    path('admin/users/<int:user_id>/reset-password/', admin_views.admin_users_send_reset_link, name='admin_users_reset_password'),
    path('admin/users/<int:user_id>/refresh-password/', admin_views.admin_users_send_reset_link, name='admin_users_refresh_password'),
    path('admin/users/<int:user_id>/provinces/', admin_views.admin_agents_provinces, name='admin_agents_provinces'),

    # Gestion des publications
    path('admin/incidents/', admin_views.admin_incidents_list, name='admin_incidents_list'),
    path('admin/incidents/<int:incident_id>/delete/', admin_views.admin_incidents_delete, name='admin_incidents_delete'),
    
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
