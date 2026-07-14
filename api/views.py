from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied

from users.models import User
from core.models import Province, Employeur, Department
from denunciations.models import Incident, PieceJointe, Commentaire, LogAudit
from .serializers import (
    UserSerializer, UserProfileSerializer, ProvinceSerializer, EmployeurSerializer,
    DepartmentSerializer, IncidentSerializer, PieceJointeSerializer, CommentaireSerializer, LogAuditSerializer
)
from .permissions import IsAdminAgentOrOwner, IsAgent, IsAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_inscription')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class ProvinceViewSet(viewsets.ModelViewSet):
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer
    permission_classes = [IsAuthenticated, IsAdminAgentOrOwner]


class EmployeurViewSet(viewsets.ModelViewSet):
    queryset = Employeur.objects.all()
    serializer_class = EmployeurSerializer
    permission_classes = [IsAuthenticated, IsAdminAgentOrOwner]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all().select_related('employeur', 'province', 'agent_assigné', 'department_assigné')
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated, IsAdminAgentOrOwner]

    def get_queryset(self):
        user = self.request.user
        qs = Incident.objects.all().select_related('employeur', 'province')
        if not user.is_authenticated:
            return qs.none()
        # Admins & Agents see all
        if (callable(getattr(user, 'is_administrateur', None)) and user.is_administrateur()) or user.is_superuser:
            return qs
        if callable(getattr(user, 'is_agent', None)) and user.is_agent():
            return qs
        # Travailleur sees only their incidents
        if getattr(user, 'role', '') == 'travailleur':
            return qs.filter(travailleur=user)
        return qs.none()

    def perform_create(self, serializer):
        request = self.request
        user = request.user
        # Assign travailleur if authenticated and role travailleur
        if user and user.is_authenticated and getattr(user, 'role', '') == 'travailleur':
            serializer.save(travailleur=user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def suivi(self, request):
        code = request.query_params.get('code') or request.query_params.get('code_suivi')
        if not code:
            return Response({'detail': 'Paramètre code manquant'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            incident = Incident.objects.get(code_suivi=code)
        except Incident.DoesNotExist:
            return Response({'detail': 'Incident introuvable'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(incident)
        return Response(serializer.data)


class PieceJointeViewSet(viewsets.ModelViewSet):
    queryset = PieceJointe.objects.all()
    serializer_class = PieceJointeSerializer
    permission_classes = [IsAuthenticated, IsAdminAgentOrOwner]


class CommentaireViewSet(viewsets.ModelViewSet):
    queryset = Commentaire.objects.all().select_related('incident', 'auteur')
    serializer_class = CommentaireSerializer
    permission_classes = [IsAuthenticated, IsAdminAgentOrOwner]

    def perform_create(self, serializer):
        user = self.request.user
        incident = serializer.validated_data.get('incident')
        # If user is travailleur, ensure they own the incident
        if getattr(user, 'role', '') == 'travailleur':
            if incident.travailleur != user:
                raise PermissionDenied('Vous ne pouvez commenter que vos propres dénonciations.')
        # set auteur if authenticated
        if user and user.is_authenticated:
            serializer.save(auteur=user)
        else:
            serializer.save()


class LogAuditViewSet(viewsets.ModelViewSet):
    queryset = LogAudit.objects.all().select_related('incident', 'utilisateur')
    serializer_class = LogAuditSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
