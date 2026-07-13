"""
URLs pour l'application denunciations.
"""

from django.urls import path, reverse
from django.views.generic.base import RedirectView


class LegacyRouteRedirectView(RedirectView):
    """Preserve historical URLs while clients move to the core namespace."""

    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse(self.pattern_name, kwargs=kwargs)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.status_code = 307
        return response

    post = get

app_name = 'denunciations'

urlpatterns = [
    # Dénonciation publique
    path('denonciation/', LegacyRouteRedirectView.as_view(pattern_name='core:incident_form'), name='incident_form'),
    path('denonciation/succes/<str:code>/', LegacyRouteRedirectView.as_view(pattern_name='core:incident_success'), name='incident_success'),
    path('rechercher/', LegacyRouteRedirectView.as_view(pattern_name='core:search_incident'), name='search_incident'),
    path('incidents/', LegacyRouteRedirectView.as_view(pattern_name='core:incidents_list'), name='incidents_list'),
    
    # Détails (nécessite authentification)
    path('detail/<str:code>/', LegacyRouteRedirectView.as_view(pattern_name='core:incident_detail'), name='incident_detail'),
    path('detail/<str:code>/statut/', LegacyRouteRedirectView.as_view(pattern_name='core:update_status'), name='update_status'),
    path('detail/<str:code>/assigner/', LegacyRouteRedirectView.as_view(pattern_name='core:assign_incident'), name='assign_incident'),
    path('detail/comment/<int:comment_id>/toggle_visibility/', LegacyRouteRedirectView.as_view(pattern_name='core:toggle_comment_visibility'), name='toggle_comment_visibility'),
    path('export/xlsx/', LegacyRouteRedirectView.as_view(pattern_name='core:export_incidents_xlsx'), name='export_incidents_xlsx'),
    path('export/<str:code>/xlsx/', LegacyRouteRedirectView.as_view(pattern_name='core:export_incident_xlsx'), name='export_incident_xlsx'),
]
