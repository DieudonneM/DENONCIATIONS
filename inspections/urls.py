from django.urls import path

from . import views

app_name = 'inspections'

urlpatterns = [
    path('soumettre/', views.MissionCreateView.as_view(), name='soumettre_mission'),
    path('ordres-de-mission/', views.OrdreDeMissionListView.as_view(), name='liste_ordres_mission'),
    path('ordre-de-mission/<int:pk>/pdf/', views.OrdreDeMissionPdfView.as_view(), name='ordre_mission_pdf'),
    path('api/entreprises/', views.search_entreprises_api, name='search_entreprises_api'),
    path('api/etablissements/', views.search_etablissements_api, name='search_etablissements_api'),
    path('api/etablissements/creer/', views.create_etablissement_api, name='create_etablissement_api'),
    path('api/check-collision/', views.check_collision_api, name='check_collision_api'),
]