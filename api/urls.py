from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    UserViewSet, ProvinceViewSet, EmployeurViewSet, DepartmentViewSet,
    IncidentViewSet, PieceJointeViewSet, CommentaireViewSet, LogAuditViewSet
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

urlpatterns = [
    path('api/', include(router.urls)),
]
