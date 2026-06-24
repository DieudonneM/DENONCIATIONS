"""
Formulaires Django pour l'application.

Contient tous les formulaires pour :
- Création de dénonciation (anonyme ou liée)
- Authentification et création de compte
- Ajout de commentaires
"""

from django import forms
from django.core.exceptions import ValidationError
from denunciations.models import Incident, Commentaire, PieceJointe, Employeur


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
            'type_incident': 'Type d\'incident *',
            'ville': 'Ville *',
            'province': 'Province *',
            'description': 'Description détaillée *',
            'email_contact_anonyme': 'Email (optionnel)',
            'telephone_contact_anonyme': 'Téléphone (optionnel)',
        }

    # Remplacer le champ employeur (FK) par un champ texte libre
    employeur = forms.CharField(
        required=True,
        label='Employeur *',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de l\'employeur ou entreprise',
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
    
    def clean(self):
        """Validation supplémentaire."""
        cleaned_data = super().clean()
        
        # Si anonyme, au moins un contact optionnel est recommandé
        est_anonyme = cleaned_data.get('est_anonyme')
        email = cleaned_data.get('email_contact_anonyme')
        telephone = cleaned_data.get('telephone_contact_anonyme')
        
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
        
        return cleaned_data

    def save(self, commit=True):
        # On gère le mapping du nom d'employeur vers l'objet Employeur
        employeur_nom = self.cleaned_data.get('employeur')
        autre = self.cleaned_data.get('autre_type_incident', '')
        fautif = self.cleaned_data.get('le_fautif', '')

        incident = super().save(commit=False)

        if employeur_nom:
            emp, created = Employeur.objects.get_or_create(nom=employeur_nom)
            incident.employeur = emp

        if incident.type_incident == 'autre' and autre:
            incident.type_incident_autre = autre

        incident.le_fautif = fautif or ''

        if commit:
            incident.save()
        return incident


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
        if len(code) < 10:
            raise ValidationError('Format de code invalide')
        return code


class FilterIncidentForm(forms.Form):
    """Formulaire pour filtrer les incidents (dashboard agent/admin)."""
    
    STATUT_CHOICES = [('', '-- Tous les statuts --')] + list(Incident.STATUT_CHOICES)
    TYPE_CHOICES = [('', '-- Tous les types --')] + list(Incident.TYPE_INCIDENT_CHOICES)
    
    statut = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    type_incident = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        label='Rechercher',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code, employeur, ville...',
        })
    )
    
    date_from = forms.DateField(
        label='À partir du',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    date_to = forms.DateField(
        label='Jusqu\'au',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
