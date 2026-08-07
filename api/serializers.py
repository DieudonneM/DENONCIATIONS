from rest_framework import serializers
from users.models import User, UserProfile
from core.models import Province, Employeur, Department
from denunciations.models import Incident, PieceJointe, Commentaire, LogAudit, MobileDeviceToken


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'date_mise_a_jour']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'telephone', 'organisation', 'date_inscription', 'provinces', 'profile']
        read_only_fields = ['date_inscription']


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'nom', 'code', 'description']


class EmployeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employeur
        fields = ['id', 'nom', 'secteur', 'description', 'ville', 'province', 'email', 'telephone', 'adresse_complete']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'nom', 'email', 'description']


class PieceJointeSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    fichier_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = PieceJointe
        fields = ['id', 'incident', 'fichier', 'url', 'fichier_url', 'download_url', 'nom_original', 'type_fichier', 'taille_fichier', 'date_ajout']
        read_only_fields = ['nom_original', 'type_fichier', 'taille_fichier', 'date_ajout']

    def _build_absolute_url(self, obj):
        request = self.context.get('request')
        fichier = getattr(obj, 'fichier', None)
        if not fichier:
            return None

        try:
            url = fichier.url
        except Exception:
            return None

        if not url:
            return None

        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_url(self, obj):
        return self._build_absolute_url(obj)

    def get_fichier_url(self, obj):
        return self._build_absolute_url(obj)

    def get_download_url(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.get_download_url())
        return obj.get_download_url()


class CommentaireSerializer(serializers.ModelSerializer):
    auteur = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Commentaire
        fields = ['id', 'incident', 'auteur', 'texte', 'type_commentaire', 'origine_public', 'date_creation']
        read_only_fields = ['date_creation']


class IncidentSerializer(serializers.ModelSerializer):
    travailleur = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='travailleur'), required=False, allow_null=True)
    travailleur_nom = serializers.SerializerMethodField()
    employeur = serializers.PrimaryKeyRelatedField(queryset=Employeur.objects.all())
    employeur_nom = serializers.SerializerMethodField()
    employeur_address = serializers.SerializerMethodField()
    agent_assigne = serializers.PrimaryKeyRelatedField(source='agent_assigné', queryset=User.objects.filter(role='agent'), required=False, allow_null=True)
    agent_assigne_nom = serializers.SerializerMethodField()
    department_assigne = serializers.PrimaryKeyRelatedField(source='department_assigné', queryset=Department.objects.all(), required=False, allow_null=True)
    department_assigne_nom = serializers.SerializerMethodField()
    province = serializers.PrimaryKeyRelatedField(queryset=Province.objects.all(), required=False, allow_null=True)
    province_nom = serializers.SerializerMethodField()
    pieces_jointes = PieceJointeSerializer(many=True, read_only=True)
    commentaires_publics = serializers.SerializerMethodField()
    commentaires_reponses_denonciateur = serializers.SerializerMethodField()
    nombre_commentaires_publics = serializers.SerializerMethodField()
    nombre_reponses_denonciateur = serializers.SerializerMethodField()
    dernier_commentaire_public_at = serializers.SerializerMethodField()
    dernier_reponse_denonciateur_at = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'code_suivi', 'travailleur', 'travailleur_nom', 'employeur', 'employeur_nom', 'employeur_address', 'ville', 'province', 'province_nom',
            'type_incident', 'type_incident_autre', 'le_fautif', 'description', 'statut', 'agent_assigne', 'agent_assigne_nom',
            'department_assigne', 'department_assigne_nom', 'est_anonyme', 'email_contact_anonyme', 'telephone_contact_anonyme',
            'accepted_privacy', 'accepted_privacy_at', 'date_creation', 'date_modification', 'date_resolution',
            'est_lu', 'pieces_jointes', 'commentaires_publics', 'commentaires_reponses_denonciateur',
            'nombre_commentaires_publics', 'nombre_reponses_denonciateur',
            'dernier_commentaire_public_at', 'dernier_reponse_denonciateur_at'
        ]
        read_only_fields = ['code_suivi', 'date_creation', 'date_modification']

    def get_employeur_address(self, obj):
        if obj.employeur:
            return getattr(obj.employeur, 'adresse_complete', '')
        return ''

    def get_travailleur_nom(self, obj):
        if obj.travailleur:
            full_name = f'{getattr(obj.travailleur, "first_name", "").strip()} {getattr(obj.travailleur, "last_name", "").strip()}'.strip()
            if full_name:
                return full_name
            return getattr(obj.travailleur, 'username', '')
        return ''

    def get_employeur_nom(self, obj):
        if obj.employeur:
            return getattr(obj.employeur, 'nom', '')
        return ''

    def get_agent_assigne_nom(self, obj):
        agent = getattr(obj, 'agent_assigné', None)
        if agent:
            full_name = f'{getattr(agent, "first_name", "").strip()} {getattr(agent, "last_name", "").strip()}'.strip()
            if full_name:
                return full_name
            return getattr(agent, 'username', '')
        return ''

    def get_department_assigne_nom(self, obj):
        department = getattr(obj, 'department_assigné', None)
        if department:
            return getattr(department, 'nom', '')
        return ''

    def get_province_nom(self, obj):
        if obj.province:
            return getattr(obj.province, 'nom', '')
        return ''

    def get_commentaires_publics(self, obj):
        comments = obj.commentaires.filter(
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_MINISTERE,
        ).select_related('auteur').order_by('-date_creation')[:5]
        messages = []
        for comment in comments:
            author = getattr(comment, 'auteur', None)
            author_name = 'Ministère'
            if author is not None:
                full_name = f'{getattr(author, "first_name", "").strip()} {getattr(author, "last_name", "").strip()}'.strip()
                if full_name:
                    author_name = full_name
                elif getattr(author, 'username', ''):
                    author_name = getattr(author, 'username')

            messages.append({
                'id': comment.id,
                'texte': comment.texte,
                'auteur_nom': author_name,
                'emetteur_type': 'ministere',
                'date_creation': comment.date_creation.isoformat() if comment.date_creation else None,
            })

        return messages

    def get_commentaires_reponses_denonciateur(self, obj):
        comments = obj.commentaires.filter(
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_DENONCIATEUR,
        ).select_related('auteur').order_by('-date_creation')[:5]
        messages = []
        for comment in comments:
            messages.append({
                'id': comment.id,
                'texte': comment.texte,
                'auteur_nom': comment.get_auteur_display(),
                'emetteur_type': 'denonciateur',
                'date_creation': comment.date_creation.isoformat() if comment.date_creation else None,
            })
        return messages

    def get_nombre_commentaires_publics(self, obj):
        return obj.commentaires.filter(
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_MINISTERE,
        ).count()

    def get_nombre_reponses_denonciateur(self, obj):
        return obj.commentaires.filter(
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_DENONCIATEUR,
        ).count()

    def get_dernier_commentaire_public_at(self, obj):
        last_comment = obj.commentaires.filter(
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_MINISTERE,
        ).order_by('-date_creation').first()
        if last_comment and last_comment.date_creation:
            return last_comment.date_creation.isoformat()
        return None

    def get_dernier_reponse_denonciateur_at(self, obj):
        last_comment = obj.commentaires.filter(
            type_commentaire=Commentaire.EST_PUBLIC,
            origine_public=Commentaire.ORIGINE_DENONCIATEUR,
        ).order_by('-date_creation').first()
        if last_comment and last_comment.date_creation:
            return last_comment.date_creation.isoformat()
        return None

    def to_representation(self, instance):
        """
        Retourne les champs employeur/province en libellés lisibles,
        tout en exposant aussi les IDs pour compatibilité client.
        """
        data = super().to_representation(instance)

        employeur_obj = getattr(instance, 'employeur', None)
        if employeur_obj is not None:
            data['employeur_id'] = data.get('employeur')
            data['employeur'] = getattr(employeur_obj, 'nom', '') or data.get('employeur')
            if not data.get('employeur_nom'):
                data['employeur_nom'] = data['employeur']

        province_obj = getattr(instance, 'province', None)
        if province_obj is not None:
            data['province_id'] = data.get('province')
            data['province'] = getattr(province_obj, 'nom', '') or data.get('province')
            if not data.get('province_nom'):
                data['province_nom'] = data['province']

        return data

    def validate(self, data):
        # If est_anonyme is False, require travailleur (identity) or at least an associated user
        est_anonyme = data.get('est_anonyme', getattr(self.instance, 'est_anonyme', True))
        travailleur = data.get('travailleur', getattr(self.instance, 'travailleur', None))
        if est_anonyme is False and not travailleur:
            raise serializers.ValidationError('Lorsque "est_anonyme" est False, le champ "travailleur" doit être renseigné (identité du dénonciateur).')
        return data

    def create(self, validated_data):
        # code_suivi generation is handled by model.save() but ensure we can assign travailleur if request present
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and getattr(request.user, 'role', '') == 'travailleur':
            validated_data.setdefault('travailleur', request.user)
        incident = Incident.objects.create(**validated_data)
        return incident


class LogAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAudit
        fields = ['id', 'incident', 'utilisateur', 'action', 'description', 'ancienne_valeur', 'nouvelle_valeur', 'date_creation']
        read_only_fields = ['date_creation']


class MobileDeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileDeviceToken
        fields = ['token', 'platform', 'code_suivi', 'is_active']
        read_only_fields = ['is_active']
        extra_kwargs = {
            'token': {'validators': []},
        }

    def validate_token(self, value):
        token = (value or '').strip()
        if not token:
            raise serializers.ValidationError('Le token est obligatoire.')
        return token

    def validate_code_suivi(self, value):
        code = (value or '').strip().upper()
        if not code:
            return ''

        if not Incident.objects.filter(code_suivi=code).exists():
            raise serializers.ValidationError('Code de suivi introuvable.')
        return code
