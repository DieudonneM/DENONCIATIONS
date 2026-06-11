"""
Formulaires pour l'application denunciations.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Incident, Commentaire, PieceJointe


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
            'employeur',
            'ville',
            'province',
            'description',
            'email_contact_anonyme',
            'telephone_contact_anonyme',
            'est_anonyme'
        ]
        widgets = {
            'type_incident': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'employeur': forms.Select(attrs={
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
            'employeur': 'Employeur *',
            'ville': 'Ville *',
            'province': 'Province *',
            'description': 'Description détaillée *',
            'email_contact_anonyme': 'Email (optionnel)',
            'telephone_contact_anonyme': 'Téléphone (optionnel)',
        }
    
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
        
        # Au moins un employeur
        if not cleaned_data.get('employeur'):
            raise ValidationError('Sélectionnez un employeur.')
        
        # Au moins une province
        if not cleaned_data.get('province'):
            raise ValidationError('Sélectionnez une province.')
        
        # Description requise
        if not cleaned_data.get('description') or len(cleaned_data.get('description', '').strip()) < 10:
            raise ValidationError('La description doit contenir au moins 10 caractères.')
        
        return cleaned_data


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
    
    search = forms.CharField(
        label='Rechercher',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Code, employeur, ville...',
        })
    )
