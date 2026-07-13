"""
Formulaires personnalisés pour l'administration (gestion des utilisateurs, provinces, entreprises).
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from users.models import User
from .models import Province, Employeur


class AdminUserCreateForm(UserCreationForm):
    """Formulaire de création d'un nouvel utilisateur par l'admin."""

    provinces = forms.ModelMultipleChoiceField(
        queryset=Province.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Provinces assignées',
        required=False,
        help_text='Attribuez des provinces à cet agent si applicable.'
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'telephone', 'organisation', 'provinces')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'exemple@email.com'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
        self.fields['role'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['telephone'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '+243 XX XXX XXXX'
        })
        self.fields['organisation'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Organisation'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self.save_m2m()
            provinces = self.cleaned_data.get('provinces')
            if provinces is not None:
                user.provinces.set(provinces)
        return user


class AdminUserEditForm(forms.ModelForm):
    """Formulaire de modification d'un utilisateur par l'admin."""

    provinces = forms.ModelMultipleChoiceField(
        queryset=Province.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Provinces assignées',
        required=False,
        help_text='Attribuez des provinces à cet agent si applicable.'
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'telephone', 'organisation', 'is_active', 'provinces')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['provinces'].initial = self.instance.provinces.all()

        for field_name, field in self.fields.items():
            if field_name != 'provinces':
                field.widget.attrs.update({
                    'class': 'form-control'
                })
        
        # Rendre email en lecture seule
        self.fields['email'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            provinces = self.cleaned_data.get('provinces')
            if provinces is not None:
                user.provinces.set(provinces)
        return user


class AdminAgentProvinceForm(forms.ModelForm):
    """Formulaire pour assigner les provinces à un agent."""
    
    provinces = forms.ModelMultipleChoiceField(
        queryset=Province.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Provinces assignées',
        required=False
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'provinces')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['provinces'].initial = self.instance.provinces.all()
        
        for field_name, field in self.fields.items():
            if field_name != 'provinces':
                field.widget.attrs.update({'class': 'form-control'})
                field.widget.attrs['readonly'] = True


class ProvinceForm(forms.ModelForm):
    """Formulaire de création/modification de province."""
    
    class Meta:
        model = Province
        fields = ('nom', 'code', 'description')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nom'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom de la province'
        })
        self.fields['code'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Code (ex: KIN, KAT, NOR)',
            'maxlength': '10'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Description (optionnel)',
            'rows': 3
        })


class EmployeurForm(forms.ModelForm):
    """Formulaire de création/modification d'entreprise."""
    
    class Meta:
        model = Employeur
        fields = ('nom', 'secteur', 'description', 'ville', 'province', 'email', 'telephone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nom'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom de l\'entreprise'
        })
        self.fields['secteur'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Description (optionnel)',
            'rows': 3
        })
        self.fields['ville'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ville'
        })
        self.fields['province'].widget.attrs.update({
            'class': 'form-control'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'contact@entreprise.com'
        })
        self.fields['telephone'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '+243 XX XXX XXXX'
        })


class UserSearchForm(forms.Form):
    """Formulaire de recherche d'utilisateurs."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par email, nom...'
        })
    )
    
    role = forms.ChoiceField(
        required=False,
        choices=[('', '-- Tous les rôles --')] + list(User.ROLE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class ProvinceSearchForm(forms.Form):
    """Formulaire de recherche de provinces."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom ou code...'
        })
    )


class EmployeurSearchForm(forms.Form):
    """Formulaire de recherche d'entreprises."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, secteur...'
        })
    )
    
    secteur = forms.ChoiceField(
        required=False,
        choices=[('', '-- Tous les secteurs --')] + list(Employeur.SECTEUR_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
