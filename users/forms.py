"""
Formulaires pour l'authentification et gestion des utilisateurs.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    """Formulaire d'authentification par email."""
    
    username = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com',
            'autofocus': True,
            'autocomplete': 'email',
        })
    )
    
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe',
            'autocomplete': 'current-password',
        })
    )
    
    def clean_username(self):
        """Accepter email comme username."""
        email = self.cleaned_data.get('username')
        if email:
            try:
                user = User.objects.get(email=email)
                self.cleaned_data['username'] = user.username
            except User.DoesNotExist:
                raise ValidationError('Cet email n\'existe pas dans notre système.')
        return self.cleaned_data.get('username')


class UserRegistrationForm(UserCreationForm):
    """Formulaire d'inscription pour les travailleurs."""
    
    email = forms.EmailField(
        label='Adresse email',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com',
            'autocomplete': 'email',
        })
    )
    
    first_name = forms.CharField(
        label='Prénom',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jean',
            'autocomplete': 'given-name',
        })
    )
    
    last_name = forms.CharField(
        label='Nom',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Doe',
            'autocomplete': 'family-name',
        })
    )
    
    telephone = forms.CharField(
        label='Téléphone (optionnel)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243 123 456 789',
            'autocomplete': 'tel',
        })
    )
    
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Au moins 8 caractères',
            'autocomplete': 'new-password',
        }),
        help_text='Au moins 8 caractères, avec lettres et chiffres'
    )
    
    password2 = forms.CharField(
        label='Confirmer mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe',
            'autocomplete': 'new-password',
        }),
        help_text='Doit correspondre au mot de passe ci-dessus'
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'telephone', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer un username à partir de l'email
        self.fields.pop('username', None)
    
    def clean_email(self):
        """Vérifier que l'email est unique."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Cet email est déjà utilisé. Veuillez vous connecter ou utiliser un autre email.')
        return email
    
    def clean_password2(self):
        """Vérifier que les deux mots de passe correspondent."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Les mots de passe ne correspondent pas.')
        
        return password2
    
    def save(self, commit=True):
        """Créer l'utilisateur avec un username généré."""
        user = super().save(commit=False)
        
        # Générer un username unique à partir de l'email
        email_prefix = self.cleaned_data['email'].split('@')[0]
        username = email_prefix
        counter = 1
        
        while User.objects.filter(username=username).exists():
            username = f"{email_prefix}{counter}"
            counter += 1
        
        user.username = username
        user.role = 'travailleur'
        user.is_active = True
        
        if commit:
            user.save()
        
        return user


class UserProfileForm(forms.ModelForm):
    """Formulaire pour éditer le profil utilisateur."""
    
    first_name = forms.CharField(
        label='Prénom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )
    
    last_name = forms.CharField(
        label='Nom',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
        })
    )
    
    email = forms.EmailField(
        label='Email (non modifiable)',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'readonly': True,
        })
    )
    
    telephone = forms.CharField(
        label='Téléphone',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243 123 456 789',
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'telephone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
