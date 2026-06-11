"""
Vues d'authentification pour l'application users.
"""

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User
from .forms import EmailAuthenticationForm, UserRegistrationForm, UserProfileForm


class LoginView(View):
    """Vue de connexion par email."""
    
    template_name = 'users/auth/login.html'
    form_class = EmailAuthenticationForm
    
    def get(self, request):
        """Afficher le formulaire de connexion."""
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Connexion'
        })
    
    def post(self, request):
        """Traiter la connexion."""
        form = self.form_class(request, data=request.POST)
        
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='users.auth_backends.EmailBackend')
            
            messages.success(request, f'Bienvenue {user.first_name or user.email} !')
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Connexion'
        })


class RegisterView(View):
    """Vue d'inscription pour les travailleurs."""
    
    template_name = 'users/auth/register.html'
    form_class = UserRegistrationForm
    
    def get(self, request):
        """Afficher le formulaire d'inscription."""
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Créer un compte'
        })
    
    def post(self, request):
        """Traiter l'inscription."""
        form = self.form_class(request.POST)
        
        if form.is_valid():
            user = form.save()
            
            # Connexion automatique
            login(request, user, backend='users.auth_backends.EmailBackend')
            messages.success(
                request,
                f'Bienvenue {user.first_name} ! Votre compte a été créé avec succès.'
            )
            
            return redirect('core:dashboard')
        
        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Créer un compte'
        })


class LogoutView(View):
    """Vue de déconnexion."""
    
    def get(self, request):
        """Déconnecter l'utilisateur."""
        logout(request)
        messages.success(request, 'Vous avez été déconnecté avec succès.')
        return redirect('core:home')


class ProfileView(LoginRequiredMixin, View):
    """Vue du profil utilisateur."""
    
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    login_url = 'users:login'
    
    def get(self, request):
        """Afficher le profil."""
        form = self.form_class(instance=request.user)
        return render(request, self.template_name, {
            'form': form,
            'user': request.user,
            'page_title': 'Mon profil'
        })
    
    def post(self, request):
        """Mettre à jour le profil."""
        form = self.form_class(request.POST, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour.')
            return redirect('users:profile')
        
        return render(request, self.template_name, {
            'form': form,
            'user': request.user,
            'page_title': 'Mon profil'
        })
