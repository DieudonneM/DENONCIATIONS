from rest_framework import viewsets, status
import logging
import re
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
import mimetypes
from django.conf import settings
from django.core.files.storage import FileSystemStorage

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


def _resolve_mobile_bearer_user(request):
    """Resolve user from mobile Bearer token format: session-<user_id>."""
    user = getattr(request, 'user', None)
    if user is not None and user.is_authenticated:
        return user

    header = str(request.headers.get('Authorization', '') or '').strip()
    if not header.lower().startswith('bearer '):
        return None

    token = header[7:].strip()
    match = re.fullmatch(r'session-(\d+)', token)
    if not match:
        return None

    user_id = int(match.group(1))
    return User.objects.filter(id=user_id, is_active=True).first()


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


def _extract_uploaded_attachments(files_dict):
    """Extract uploaded files from common multipart field names used by web/mobile clients."""
    candidates = ('pieces_jointes', 'pieces_jointes[]', 'files', 'files[]')
    files = []
    for key in candidates:
        files.extend(files_dict.getlist(key))

    # Deduplicate while preserving order.
    unique_files = []
    seen_ids = set()
    for file in files:
        file_id = id(file)
        if file_id in seen_ids:
            continue
        seen_ids.add(file_id)
        unique_files.append(file)
    return unique_files


def _build_public_incident_payload(incident):
    """Return a stable subset used by mobile clients without traversing optional serializer fields."""
    return {
        'id': incident.id,
        'code_suivi': incident.code_suivi,
        'statut': incident.statut,
        'date_creation': incident.date_creation.isoformat() if incident.date_creation else None,
        'date_modification': incident.date_modification.isoformat() if incident.date_modification else None,
        'employeur': incident.employeur.nom if getattr(incident, 'employeur', None) else '',
        'employeur_nom': incident.employeur.nom if getattr(incident, 'employeur', None) else '',
        'employeur_address': getattr(getattr(incident, 'employeur', None), 'adresse_complete', '') if getattr(incident, 'employeur', None) else '',
        'ville': incident.ville,
        'province': incident.province.nom if getattr(incident, 'province', None) else '',
        'province_nom': incident.province.nom if getattr(incident, 'province', None) else '',
        'type_incident': incident.type_incident,
        'type_incident_autre': incident.type_incident_autre,
        'description': incident.description,
        'le_fautif': incident.le_fautif,
        'est_anonyme': incident.est_anonyme,
        'email_contact_anonyme': incident.email_contact_anonyme,
        'telephone_contact_anonyme': incident.telephone_contact_anonyme,
    }


def _persist_piece_jointe_with_fallback(*, incident, uploaded_file, nom_original, type_fichier, taille_fichier):
    """Try default storage first, then fallback to local media storage if backend upload fails."""
    try:
        return PieceJointe.objects.create(
            incident=incident,
            fichier=uploaded_file,
            nom_original=nom_original,
            type_fichier=type_fichier,
            taille_fichier=taille_fichier,
        )
    except Exception as primary_error:
        logging.getLogger(__name__).warning(
            'Primary attachment storage failed for %s: %s. Falling back to local storage.',
            nom_original,
            primary_error,
        )

        attachment = PieceJointe(
            incident=incident,
            nom_original=nom_original,
            type_fichier=type_fichier,
            taille_fichier=taille_fichier,
        )
        attachment.fichier.storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
        attachment.fichier.save(nom_original, uploaded_file, save=False)
        attachment.save()
        return attachment


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


class DeleteUserAccountView(APIView):
    """Supprime ou désactive le compte de l'utilisateur authentifié pour la conformité App Store."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, format=None):
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            return Response({'detail': 'Authentification requise.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'Ce compte a déjà été désactivé.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.is_active = False
            user.email = f'deleted+{user.id}@met-rdc.invalid'
            user.username = f'deleted_{user.id}'
            user.first_name = ''
            user.last_name = ''
            user.telephone = ''
            user.organisation = ''
            user.set_unusable_password()
            user.save(update_fields=['is_active', 'email', 'username', 'first_name', 'last_name', 'telephone', 'organisation', 'password'])
        except Exception:
            return Response({'detail': 'Impossible de supprimer ce compte pour le moment.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logout(request)
        return Response({'detail': 'Compte supprimé avec succès.'}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='staff-nouvelles')
    def staff_nouvelles(self, request):
        user = _resolve_mobile_bearer_user(request)
        if user is None:
            return Response({'detail': 'Authentification requise.'}, status=status.HTTP_401_UNAUTHORIZED)

        is_staff = bool(
            (callable(getattr(user, 'is_administrateur', None)) and user.is_administrateur())
            or (callable(getattr(user, 'is_agent', None)) and user.is_agent())
            or user.is_superuser
            or getattr(user, 'role', '') in {'agent', 'administrateur'}
        )

        if not is_staff:
            return Response({'detail': 'Accès réservé aux admins et agents.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            page = int(str(request.query_params.get('page', '1')).strip() or '1')
        except ValueError:
            page = 1
        page = max(page, 1)
        page_size = 10

        qs = (
            Incident.objects.filter(statut='nouvelle')
            .select_related('employeur', 'province', 'agent_assigné')
            .order_by('-date_creation')
        )

        total = qs.count()
        offset = (page - 1) * page_size
        rows = qs[offset : offset + page_size]

        results = [
            {
                'id': incident.id,
                'code_suivi': incident.code_suivi,
                'statut': incident.statut,
                'type_incident': incident.type_incident,
                'type_incident_display': incident.get_type_incident_display(),
                'ville': incident.ville,
                'date_creation': incident.date_creation.isoformat() if incident.date_creation else None,
                'employeur': incident.employeur.nom if incident.employeur else '',
                'employeur_nom': incident.employeur.nom if incident.employeur else '',
                'province_nom': incident.province.nom if incident.province else '',
                'agent_assigne_nom': (
                    (incident.agent_assigné.get_full_name() or incident.agent_assigné.username)
                    if incident.agent_assigné
                    else ''
                ),
            }
            for incident in rows
        ]

        return Response(
            {
                'page': page,
                'page_size': page_size,
                'total': total,
                'has_next': (offset + page_size) < total,
                'results': results,
            },
            status=status.HTTP_200_OK,
        )


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
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, format=None):
        try:
            data = _normalize_public_incident_payload(request.data)

            # The public form uses 'employeur' as a text field and 'employeur_address', 'secteur', 'autre_secteur'
            form = IncidentForm(data, files=request.FILES)
            if not form.is_valid():
                return Response({'detail': 'Validation error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                incident = form.save(commit=True)

                # Persist uploaded files for mobile/public submissions.
                files = _extract_uploaded_attachments(request.FILES)
                failed_files = []
                for file in files:
                    name = (getattr(file, 'name', '') or 'piece_jointe').strip()
                    content_type = (getattr(file, 'content_type', '') or '').strip()
                    if not content_type:
                        guessed_type, _ = mimetypes.guess_type(name)
                        content_type = guessed_type or 'application/octet-stream'

                    # Keep compatibility with deployments that may still have DB column length=50.
                    safe_content_type = content_type[:50]
                    safe_name = name[:255]
                    safe_size = getattr(file, 'size', 0) or 0

                    try:
                        _persist_piece_jointe_with_fallback(
                            incident=incident,
                            uploaded_file=file,
                            nom_original=safe_name,
                            type_fichier=safe_content_type,
                            taille_fichier=safe_size,
                        )
                    except Exception as file_error:
                        logging.getLogger(__name__).exception(
                            'Attachment save failed for %s on incident %s: %s',
                            safe_name,
                            incident.code_suivi,
                            file_error,
                        )
                        failed_files.append(safe_name)

                if files and len(failed_files) == len(files):
                    # If all attachments failed, fail explicitly to avoid silent data loss.
                    raise RuntimeError('Toutes les pièces jointes ont échoué lors de l\'enregistrement.')
        except Exception as e:
            logging.getLogger(__name__).exception('Public incident create failed: %s', e)
            return Response(
                {
                    'detail': 'Erreur serveur lors de la soumission.',
                    'error': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(_build_public_incident_payload(incident), status=status.HTTP_201_CREATED)


class PublicIncidentDetailView(APIView):
    """Endpoint public pour modifier ou supprimer une dénonciation via son code de suivi."""

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, code, format=None):
        try:
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

            return Response(_build_public_incident_payload(updated_incident), status=status.HTTP_200_OK)
        except Exception:
            logging.getLogger(__name__).exception('Public incident update failed for code=%s', code)
            return Response(
                {
                    'detail': 'Erreur serveur lors de la mise a jour.',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
        user_role = (validated.get('user_role') or '').strip().lower()
        receives_staff_notifications = bool(validated.get('receives_staff_notifications', False))

        if user_role not in {MobileDeviceToken.ROLE_AGENT, MobileDeviceToken.ROLE_ADMINISTRATEUR}:
            receives_staff_notifications = False

        incident = None
        if code_suivi:
            incident = Incident.objects.filter(code_suivi=code_suivi).first()

        obj, created = MobileDeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'platform': platform,
                'incident': incident,
                'code_suivi': code_suivi,
                'user_role': user_role,
                'receives_staff_notifications': receives_staff_notifications,
                'is_active': True,
            },
        )

        response_data = {
            'detail': 'Token enregistre' if created else 'Token mis a jour',
            'created': created,
            'platform': obj.platform,
            'code_suivi': obj.code_suivi,
            'user_role': obj.user_role,
            'receives_staff_notifications': obj.receives_staff_notifications,
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
