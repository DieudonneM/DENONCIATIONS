"""
Formulaires pour l'application denunciations.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Incident, Commentaire, PieceJointe, Employeur, Province
from django.utils import timezone


class MultipleFileInput(forms.FileInput):
    """Widget personnalisé pour upload de fichiers multiples."""
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        return super().render(name, value, attrs, renderer)


class IncidentForm(forms.ModelForm):
    """Formulaire public pour créer une dénonciation."""
    
    pieces_jointes = forms.FileField(
        required=False,
        widget=MultipleFileInput(),
        help_text='Fichiers autorisés : PDF, DOCX, Images, Vidéos, Audios (max 50 MB par fichier)'
    )
    
    # Options pour anonymat
    est_anonyme = forms.BooleanField(
        required=False,
        initial=True,
        label='Rester anonyme',
        help_text='Si coché, votre identité ne sera jamais visible pour les agents'
    )
    
    # Confirmation de la politique (preuve côté serveur)
    confirm_anonymous = forms.BooleanField(
        required=False,
        label="J'accepte la politique de confidentialité",
        widget=forms.CheckboxInput()
    )
    
    class Meta:
        model = Incident
        fields = [
            'type_incident',
            'ville',
            'province',
            'description',
            'email_contact_anonyme',
            'telephone_contact_anonyme',
            'est_anonyme',
            'le_fautif'
        ]

        widgets = {
            'type_incident': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kinshasa, Lubumbashi, etc.',
                'required': True
            }),
            'province': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Décrivez précisément l\'incident...',
                'required': True
            }),
            'email_contact_anonyme': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'exemple@email.com',
                'required': False
            }),
            'telephone_contact_anonyme': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243 123 456 789',
                'required': False
            }),
        }
        labels = {
            'type_incident': 'Type d\'incident ',
            'ville': 'Ville ',
            'province': 'Province ',
            'ville': 'Ville ',
            'province': 'Province ',
            'description': 'Description détaillée ',
            'email_contact_anonyme': 'Email (optionnel)',
            'telephone_contact_anonyme': 'Téléphone (optionnel)',
        }

    # Remplacer le champ employeur (FK) par un champ texte libre
    employeur = forms.CharField(
        required=True,
        label='Employeur Fautif',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'employeur ou entreprise',
        })
    )

    employeur_address = forms.CharField(
        required=False,
        label="Adresse complète de l'Entreprise",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': "Numéro, rue, quartier, quartier administratif, code postal (si disponible)",
            'rows': 3,
        })
    )

    # Secteur d'activité (dropdown) + option 'autre' pour précision
    secteur = forms.ChoiceField(
        required=True,
        label="Secteur d'activité",
        choices=[('', '-- Sélectionnez --')] + list(Employeur.SECTEUR_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    autre_secteur = forms.CharField(
        required=False,
        label='Précisez le secteur (si Autre)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Décrivez le secteur d\'activité',
        })
    )

    # Champs pour le dénonciateur non-anonyme (inspirés du formulaire d'inscription)
    submitter_first_name = forms.CharField(
        required=False,
        label='Prénom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom',
        })
    )

    submitter_last_name = forms.CharField(
        required=False,
        label='Nom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom',
        })
    )

    submitter_email = forms.EmailField(
        required=False,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com',
        })
    )

    submitter_telephone = forms.CharField(
        required=False,
        label='Téléphone',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243 123 456 789',
        })
    )

    # Champ pour préciser le type si 'autre' est choisi
    autre_type_incident = forms.CharField(
        required=False,
        label='Précisez (si Autre)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Précisez le type d\'incident',
        })
    )

    # Champ 'le fautif'
    le_fautif = forms.CharField(
        required=False,
        label='Le fautif (nom ou description)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom ou description du fautif (optionnel)'
        })
    )
    
    def clean_email_contact_anonyme(self):
        """Valider l'email si fourni."""
        email = self.cleaned_data.get('email_contact_anonyme')
        if email and not email.strip():
            return ''
        return email

    def clean_pieces_jointes(self):
        """Valider les fichiers joints (extensions autorisées et taille maximale)."""
        # Récupérer les fichiers téléchargés (supporte input multiple)
        files = []
        try:
            files = self.files.getlist('pieces_jointes')
        except Exception:
            files = []

        MAX_MB = 50
        allowed_exts = [ext.lower() for ext in PieceJointe.EXTENSIONS_AUTORISEES]
        invalid = []
        oversize = []

        for f in files:
            name = getattr(f, 'name', '')
            ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
            if ext and ext not in allowed_exts:
                invalid.append(name)
            if hasattr(f, 'size') and f.size > MAX_MB * 1024 * 1024:
                oversize.append(name)

        if invalid or oversize:
            messages = []
            if invalid:
                messages.append(f"Format non autorisé pour: {', '.join(invalid)}. Formats autorisés: {', '.join(allowed_exts)}.")
            if oversize:
                messages.append(f"Taille dépassée (> {MAX_MB} MB) pour: {', '.join(oversize)}.")
            raise ValidationError(' '.join(messages))

        # Retourner la valeur du champ (peut être None ou le fichier unique selon l'input)
        return self.cleaned_data.get('pieces_jointes')
    
    def clean(self):
        """Validation supplémentaire."""
        cleaned_data = super().clean()
        # Si la form a été initialisée avec un user connecté, on peut s'en servir
        user = getattr(self, 'user', None)
        
        # Si anonyme, au moins un contact optionnel est recommandé
        est_anonyme = cleaned_data.get('est_anonyme')
        email = cleaned_data.get('email_contact_anonyme')
        telephone = cleaned_data.get('telephone_contact_anonyme')
        # Champs pour le dénonciateur non-anonyme
        s_first = cleaned_data.get('submitter_first_name')
        s_last = cleaned_data.get('submitter_last_name')
        s_email = cleaned_data.get('submitter_email')
        s_tel = cleaned_data.get('submitter_telephone')
        
        # Au moins un type d'incident
        if not cleaned_data.get('type_incident'):
            raise ValidationError('Sélectionnez un type d\'incident.')

        # Au moins un employeur (texte libre)
        if not cleaned_data.get('employeur') or not cleaned_data.get('employeur').strip():
            raise ValidationError('Indiquez le nom de l\'employeur.')

        # Si type == 'autre', alors préciser
        if cleaned_data.get('type_incident') == 'autre' and not cleaned_data.get('autre_type_incident'):
            raise ValidationError('Précisez le type d\'incident lorsque vous sélectionnez Autre.')

        # Au moins une province
        if not cleaned_data.get('province'):
            raise ValidationError('Sélectionnez une province.')

        # Description requise
        if not cleaned_data.get('description') or len(cleaned_data.get('description', '').strip()) < 10:
            raise ValidationError('La description doit contenir au moins 10 caractères.')
        
        # Règles liées à l'anonymat / identité du dénonciateur
        if est_anonyme:
            # Lorsque la personne souhaite rester anonyme, elle doit fournir au moins
            # un moyen de contact : email_contact_anonyme OU telephone_contact_anonyme
            if not (email or telephone):
                raise ValidationError('Si vous choisissez de rester anonyme, indiquez au moins un moyen de contact (email et/ou téléphone).')
        else:
            # Si non-anonyme et que l'utilisateur est connecté, on prendra ses informations
            if user and getattr(user, 'is_authenticated', False):
                pass
            else:
                # Si non-anonyme et pas connecté, il faut renseigner les informations minimales du profil
                if not (s_first and s_last and s_email):
                    raise ValidationError('Si vous ne souhaitez pas rester anonyme, renseignez votre prénom, nom et adresse email.')

        # Vérifier l'acceptation de la politique de confidentialité
        confirm = cleaned_data.get('confirm_anonymous')
        if not confirm:
            self.add_error('confirm_anonymous', 'Vous devez accepter la politique de confidentialité pour soumettre une dénonciation.')
        return cleaned_data

    def save(self, commit=True):
        # On gère le mapping du nom d'employeur vers l'objet Employeur
        employeur_nom = self.cleaned_data.get('employeur')
        autre = self.cleaned_data.get('autre_type_incident', '')
        fautif = self.cleaned_data.get('le_fautif', '')

        incident = super().save(commit=False)

        if employeur_nom:
            emp, created = Employeur.objects.get_or_create(nom=employeur_nom)
            # enregistrer l'adresse complète si fournie
            adresse_val = self.cleaned_data.get('employeur_address')
            if adresse_val:
                emp.adresse_complete = adresse_val
            # assigner le secteur choisi
            secteur_val = self.cleaned_data.get('secteur')
            autre_secteur_val = self.cleaned_data.get('autre_secteur')
            if secteur_val:
                emp.secteur = secteur_val
                # si l'utilisateur a précisé un secteur librement, l'enregistrer dans la description
                if secteur_val == 'autre' and autre_secteur_val:
                    if emp.description:
                        emp.description = f"{emp.description}\nSecteur précisé: {autre_secteur_val}"
                    else:
                        emp.description = f"Secteur précisé: {autre_secteur_val}"
            emp.save()
            incident.employeur = emp

        if incident.type_incident == 'autre' and autre:
            incident.type_incident_autre = autre

        incident.le_fautif = fautif or ''

        if commit:
            # marquer l'acceptation de la politique si cochée
            incident.accepted_privacy = True
            incident.accepted_privacy_at = timezone.now()
            incident.save()
        return incident

    def __init__(self, *args, **kwargs):
        # accept an optional 'user' kwarg (request.user)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


class CommentaireForm(forms.ModelForm):
    """Formulaire pour ajouter un commentaire à une dénonciation."""
    
    class Meta:
        model = Commentaire
        fields = ['texte', 'type_commentaire']
        widgets = {
            'texte': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ajoutez un commentaire...',
                'required': True
            }),
            'type_commentaire': forms.RadioSelect(choices=[
                ('public', '🔓 Public (visible au travailleur)'),
                ('interne', '🔒 Interne (agents seulement)'),
            ]),
        }
        labels = {
            'texte': 'Commentaire *',
            'type_commentaire': 'Visibilité du commentaire *',
        }
    
    def clean_texte(self):
        """Valider que le commentaire n'est pas vide."""
        texte = self.cleaned_data.get('texte', '').strip()
        if not texte:
            raise ValidationError('Le commentaire ne peut pas être vide.')
        if len(texte) < 5:
            raise ValidationError('Le commentaire doit contenir au moins 5 caractères.')
        return texte


class SearchIncidentForm(forms.Form):
    """Formulaire pour rechercher un incident par code de suivi."""
    
    code_suivi = forms.CharField(
        label='Code de suivi',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Exemple: RDC2024ABC12345',
            'autofocus': True,
        })
    )
    
    def clean_code_suivi(self):
        """Valider le format du code."""
        code = self.cleaned_data.get('code_suivi', '').strip().upper()
        if not code.startswith('RDC'):
            raise ValidationError('Le code doit commencer par RDC')
        return code


class FilterIncidentForm(forms.Form):
    """Formulaire pour filtrer les incidents (admin/agent)."""
    
    STATUT_CHOICES = [('', '-- Tous les statuts --')] + list(Incident.STATUT_CHOICES)
    TYPE_CHOICES = [('', '-- Tous les types --')] + list(Incident.TYPE_INCIDENT_CHOICES)
    
    statut = forms.ChoiceField(
        label='Statut',
        required=False,
        choices=STATUT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    type_incident = forms.ChoiceField(
        label='Type d\'incident',
        required=False,
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    province = forms.ModelChoiceField(
        label='Province',
        required=False,
        queryset=Province.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )

    secteur = forms.ChoiceField(
        label="Secteur d'activité",
        required=False,
        choices=[('', '-- Tous les secteurs --')] + list(Employeur.SECTEUR_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    search = forms.CharField(
        label='Rechercher',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code, employeur, ville...',
        })
    )
