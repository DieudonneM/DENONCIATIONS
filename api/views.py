from rest_framework import viewsets, status
import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login

from users.models import User
from users.forms import UserRegistrationForm
from core.models import Province, Employeur, Department
from denunciations.models import Incident, PieceJointe, Commentaire, LogAudit
from .serializers import (
    UserSerializer, UserProfileSerializer, ProvinceSerializer, EmployeurSerializer,
    DepartmentSerializer, IncidentSerializer, PieceJointeSerializer, CommentaireSerializer, LogAuditSerializer
)
from rest_framework.views import APIView
from django.utils.text import slugify
from denunciations.forms import IncidentForm
from .permissions import IsAdminAgentOrOwner, IsAdmin


class ApiLoginView(APIView):
    """Connexion mobile via JSON (email + mot de passe)."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        email = str(request.data.get('email', '')).strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'detail': 'Email et mot de passe requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {'detail': 'Identifiants invalides.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user, backend='users.auth_backends.EmailBackend')
        return Response(
            {
                'token': f'session-{user.id}',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class ApiRegisterView(APIView):
    """Inscription mobile via JSON."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        raw_password = request.data.get('password') or request.data.get('password1')
        payload = {
            'email': str(request.data.get('email', '')).strip(),
            'first_name': str(request.data.get('first_name', '')).strip(),
            'last_name': str(request.data.get('last_name', '')).strip(),
            'telephone': str(request.data.get('phone') or request.data.get('telephone') or '').strip(),
            'password1': raw_password or '',
            'password2': request.data.get('password2') or raw_password or '',
        }

        form = UserRegistrationForm(payload)
        if not form.is_valid():
            return Response(
                {'detail': 'Validation error', 'errors': form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = form.save()
        return Response(
            {
                'detail': 'Compte créé avec succès.',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )


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
        logger = logging.getLogger(__name__)
        logger.info(f"suivi endpoint called: method={request.method} params={request.query_params}")
        code = request.query_params.get('code') or request.query_params.get('code_suivi')
        if not code:
            return Response({'detail': 'Paramètre code manquant'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            incident = Incident.objects.get(code_suivi=code)
            serializer = self.get_serializer(incident)
            return Response(serializer.data)
        except Incident.DoesNotExist:
            logger.info(f"suivi: incident not found for code={code}")
            return Response({'detail': 'Incident introuvable'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Log full exception traceback and return JSON error to clients (avoid HTML debug page)
            logger.exception(f"Error while processing suivi for code={code}: {e}")
            return Response({'detail': 'Erreur serveur', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


class PublicIncidentCreate(APIView):
    """Endpoint public pour créer une dénonciation depuis des clients non-authentifiés (mobile)."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = request.data.copy()
        # Normalize province: allow sending province name or id and create it if needed.
        province_val = data.get('province')
        if province_val:
            province_text = str(province_val).strip()
            if province_text.isdigit():
                data['province'] = int(province_text)
            elif province_text:
                try:
                    prov = Province.objects.filter(nom__iexact=province_text).first()
                    if prov:
                        data['province'] = prov.id
                    else:
                        base_code = slugify(province_text).upper()[:8] or 'PROVINCE'
                        code = base_code
                        suffix = 1
                        while Province.objects.filter(code=code).exists():
                            code = f'{base_code}{suffix}'
                            suffix += 1
                        prov = Province.objects.create(nom=province_text, code=code)
                        data['province'] = prov.id
                except Exception:
                    data['province'] = ''
            else:
                data['province'] = ''

        # Normalize secteur: if provided but not matching choice slugs, set to 'autre'
        secteur_val = data.get('secteur')
        allowed_secteurs = [s[0] for s in Employeur.SECTEUR_CHOICES]
        if secteur_val and secteur_val not in allowed_secteurs:
            data['secteur'] = 'autre'

        # Map mobile-friendly type labels to backend keys
        type_map = {
            'Non-paiement': 'salaire',
            'Discrimination': 'discrimination',
            'Violence': 'harcèlement',
            'Harcèlement': 'harcèlement',
            'Autre': 'autre'
        }
        t = data.get('type_incident')
        if t and t in type_map:
            data['type_incident'] = type_map[t]

        # The public form uses 'employeur' as a text field and 'employeur_address', 'secteur', 'autre_secteur'
        form = IncidentForm(data, files=request.FILES)
        if not form.is_valid():
            return Response({'detail': 'Validation error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        incident = form.save(commit=True)
        serializer = IncidentSerializer(incident, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
