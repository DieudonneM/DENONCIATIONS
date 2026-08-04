from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    UserViewSet, ProvinceViewSet, EmployeurViewSet, DepartmentViewSet,
    IncidentViewSet, PieceJointeViewSet, CommentaireViewSet, LogAuditViewSet,
    PublicIncidentCreate, PublicIncidentDetailView, ApiLoginView, ApiRegisterView, PublicDeviceTokenRegisterView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'provinces', ProvinceViewSet, basename='province')
router.register(r'employeurs', EmployeurViewSet, basename='employeur')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'pieces-jointe', PieceJointeViewSet, basename='piecejointe')
router.register(r'commentaires', CommentaireViewSet, basename='commentaire')
router.register(r'logs', LogAuditViewSet, basename='logaudit')

app_name = 'api'

urlpatterns = [
    # The project-level urls.py will include this module under the '/api/' prefix.
    path('login/', ApiLoginView.as_view(), name='api_login'),
    path('register/', ApiRegisterView.as_view(), name='api_register'),
    path('', include(router.urls)),
    path('public/incidents/', PublicIncidentCreate.as_view(), name='public_incident_create'),
    path('public/incidents/<str:code>/', PublicIncidentDetailView.as_view(), name='public_incident_detail'),
    path('public/device-tokens/', PublicDeviceTokenRegisterView.as_view(), name='public_device_token_register'),
    path('public/device-tokens/deactivate/', PublicDeviceTokenRegisterView.as_view(), name='public_device_token_deactivate'),
]
