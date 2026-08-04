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
from denunciations.models import Incident, PieceJointe, Commentaire, LogAudit, MobileDeviceToken
from .serializers import (
    UserSerializer, UserProfileSerializer, ProvinceSerializer, EmployeurSerializer,
    DepartmentSerializer, IncidentSerializer, PieceJointeSerializer, CommentaireSerializer, LogAuditSerializer,
    MobileDeviceTokenSerializer,
)
from rest_framework.views import APIView
from django.utils.text import slugify
from denunciations.forms import IncidentForm
from .permissions import IsAdminAgentOrOwner, IsAdmin


def _normalize_public_incident_payload(data):
    """Normalize mobile/public payload fields before binding the incident form."""
    payload = data.copy()

    province_val = payload.get('province')
    if province_val:
        province_text = str(province_val).strip()
        if province_text.isdigit():
            payload['province'] = int(province_text)
        elif province_text:
            try:
                prov = Province.objects.filter(nom__iexact=province_text).first()
                if prov:
                    payload['province'] = prov.id
                else:
                    base_code = slugify(province_text).upper()[:8] or 'PROVINCE'
                    code = base_code
                    suffix = 1
                    while Province.objects.filter(code=code).exists():
                        code = f'{base_code}{suffix}'
                        suffix += 1
                    prov = Province.objects.create(nom=province_text, code=code)
                    payload['province'] = prov.id
            except Exception:
                payload['province'] = ''
        else:
            payload['province'] = ''

    secteur_val = payload.get('secteur')
    allowed_secteurs = [s[0] for s in Employeur.SECTEUR_CHOICES]
    if secteur_val and secteur_val not in allowed_secteurs:
        payload['secteur'] = 'autre'

    type_map = {
        'Non-paiement': 'salaire',
        'Discrimination': 'discrimination',
        'Violence': 'harcèlement',
        'Harcèlement': 'harcèlement',
        'Autre': 'autre'
    }
    incident_type = payload.get('type_incident')
    if incident_type and incident_type in type_map:
        payload['type_incident'] = type_map[incident_type]

    payload['confirm_anonymous'] = payload.get('confirm_anonymous', True)
    return payload


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

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def repondre(self, request):
        code = (request.data.get('code') or request.data.get('code_suivi') or '').strip().upper()
        texte = (request.data.get('texte') or request.data.get('message') or '').strip()

        if not code:
            return Response({'detail': 'Paramètre code manquant.'}, status=status.HTTP_400_BAD_REQUEST)
        if not texte:
            return Response({'detail': 'Le message est obligatoire.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(texte) < 3:
            return Response({'detail': 'Le message doit contenir au moins 3 caractères.'}, status=status.HTTP_400_BAD_REQUEST)

        incident = Incident.objects.filter(code_suivi=code).first()
        if incident is None:
            return Response({'detail': 'Incident introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        auteur = None
        user = request.user
        if user and user.is_authenticated:
            if getattr(user, 'role', '') in {'agent', 'administrateur'} or user.is_superuser:
                return Response({'detail': 'Cette action est réservée au dénonciateur.'}, status=status.HTTP_403_FORBIDDEN)
            if getattr(user, 'role', '') == 'travailleur' and incident.travailleur_id and incident.travailleur_id != user.id:
                return Response({'detail': 'Ce code ne correspond pas à votre dossier.'}, status=status.HTTP_403_FORBIDDEN)
            if getattr(user, 'role', '') == 'travailleur':
                auteur = user

        commentaire = Commentaire.objects.create(
            incident=incident,
            auteur=auteur,
            texte=texte,
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_DENONCIATEUR,
        )

        previous_status = incident.statut
        if incident.statut == 'attente':
            incident.statut = 'analyse'
            incident.save(update_fields=['statut'])

        try:
            LogAudit.objects.create(
                incident=incident,
                utilisateur=auteur,
                action='ajout_commentaire',
                description=f'Réponse du dénonciateur via API publique: {commentaire.texte[:200]}',
                ancienne_valeur='',
                nouvelle_valeur=commentaire.texte[:200],
            )
        except Exception:
            pass

        if previous_status != incident.statut:
            try:
                LogAudit.objects.create(
                    incident=incident,
                    utilisateur=auteur,
                    action='modification_statut',
                    description='Statut changé automatiquement de attente à analyse après réponse du dénonciateur.',
                    ancienne_valeur=previous_status,
                    nouvelle_valeur=incident.statut,
                )
            except Exception:
                pass

        return Response(
            {
                'detail': 'Réponse enregistrée.',
                'commentaire_id': commentaire.id,
                'date_creation': commentaire.date_creation.isoformat() if commentaire.date_creation else None,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def dashboard_stats(self, request):
        user = request.user
        is_staff = bool(
            user.is_authenticated and (
                getattr(user, 'role', '') in {'agent', 'administrateur'}
                or user.is_superuser
            )
        )
        if not is_staff:
            if request.headers.get('Authorization'):
                return Response({'detail': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)
            return Response({'detail': 'Accès refusé'}, status=status.HTTP_403_FORBIDDEN)

        incidents = Incident.objects.all()
        return Response({
            'total': incidents.count(),
            'nouvelle': incidents.filter(statut='nouvelle').count(),
            'analyse': incidents.filter(statut='analyse').count(),
            'attente': incidents.filter(statut='attente').count(),
            'resolue': incidents.filter(statut='resolue').count(),
            'classée': incidents.filter(statut='classée').count(),
            'non_lues': incidents.filter(est_lu=False).count(),
            'anonymes': incidents.filter(est_anonyme=True).count(),
            'recent': [
                {
                    'code_suivi': incident.code_suivi,
                    'employeur': incident.employeur.nom if incident.employeur else '',
                    'type_incident': incident.get_type_incident_display(),
                    'statut': incident.statut,
                    'date_creation': incident.date_creation.isoformat(),
                }
                for incident in incidents.order_by('-date_creation')[:10]
            ],
        })


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
        origine_public = Commentaire.ORIGINE_MINISTERE
        if getattr(user, 'role', '') == 'travailleur':
            origine_public = Commentaire.ORIGINE_DENONCIATEUR
        if user and user.is_authenticated:
            serializer.save(auteur=user, origine_public=origine_public)
        else:
            serializer.save(origine_public=origine_public)


class LogAuditViewSet(viewsets.ModelViewSet):
    queryset = LogAudit.objects.all().select_related('incident', 'utilisateur')
    serializer_class = LogAuditSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class PublicIncidentCreate(APIView):
    """Endpoint public pour créer une dénonciation depuis des clients non-authentifiés (mobile)."""
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        data = _normalize_public_incident_payload(request.data)

        # The public form uses 'employeur' as a text field and 'employeur_address', 'secteur', 'autre_secteur'
        form = IncidentForm(data, files=request.FILES)
        if not form.is_valid():
            return Response({'detail': 'Validation error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        incident = form.save(commit=True)

        # Persist uploaded files for mobile/public submissions.
        files = request.FILES.getlist('pieces_jointes')
        for file in files:
            PieceJointe.objects.create(
                incident=incident,
                fichier=file,
                nom_original=getattr(file, 'name', '') or 'piece_jointe',
                type_fichier=getattr(file, 'content_type', '') or '',
                taille_fichier=getattr(file, 'size', 0) or 0,
            )

        serializer = IncidentSerializer(incident, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PublicIncidentDetailView(APIView):
    """Endpoint public pour modifier ou supprimer une dénonciation via son code de suivi."""

    permission_classes = [AllowAny]

    def patch(self, request, code, format=None):
        incident = Incident.objects.filter(code_suivi=code).first()
        if incident is None:
            return Response({'detail': 'Incident introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        data = _normalize_public_incident_payload(request.data)
        form = IncidentForm(data, files=request.FILES, instance=incident)
        if not form.is_valid():
            return Response({'detail': 'Validation error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

        updated_incident = form.save(commit=True)
        try:
            LogAudit.objects.create(
                incident=updated_incident,
                utilisateur=None,
                action='modification_statut',
                description='Modification publique depuis l\'application mobile.',
                ancienne_valeur='',
                nouvelle_valeur='incident_updated',
            )
        except Exception:
            pass

        serializer = IncidentSerializer(updated_incident, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, code, format=None):
        incident = Incident.objects.filter(code_suivi=code).first()
        if incident is None:
            return Response({'detail': 'Incident introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            LogAudit.objects.create(
                incident=incident,
                utilisateur=None,
                action='suppression',
                description='Suppression publique depuis l\'application mobile.',
                ancienne_valeur=incident.code_suivi,
                nouvelle_valeur='',
            )
        except Exception:
            pass

        incident.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicDeviceTokenRegisterView(APIView):
    """Enregistrer/mettre a jour un token FCM pour les notifications de suivi."""

    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = MobileDeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        token = validated['token']
        platform = validated.get('platform') or MobileDeviceToken.PLATFORM_OTHER
        code_suivi = (validated.get('code_suivi') or '').strip().upper()

        incident = None
        if code_suivi:
            incident = Incident.objects.filter(code_suivi=code_suivi).first()

        obj, created = MobileDeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'platform': platform,
                'incident': incident,
                'code_suivi': code_suivi,
                'is_active': True,
            },
        )

        response_data = {
            'detail': 'Token enregistre' if created else 'Token mis a jour',
            'created': created,
            'platform': obj.platform,
            'code_suivi': obj.code_suivi,
            'is_active': obj.is_active,
        }
        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, format=None):
        token = str(request.data.get('token') or request.query_params.get('token') or '').strip()
        if not token:
            return Response({'detail': 'Token requis.'}, status=status.HTTP_400_BAD_REQUEST)

        updated = MobileDeviceToken.objects.filter(token=token).update(is_active=False)
        if updated == 0:
            return Response({'detail': 'Token introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'detail': 'Token desactive.', 'updated': updated}, status=status.HTTP_200_OK)
