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
from django.urls import reverse
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta


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
            
            # Si l'utilisateur doit changer son mot de passe, vérifier sa validité
            if getattr(user, 'must_change_password', False):
                # vérifier expiration (5 minutes)
                t0 = getattr(user, 'temp_password_set_at', None)
                if t0 and (timezone.now() - t0) <= timedelta(minutes=5):
                    messages.info(request, 'Vous devez changer votre mot de passe avant de continuer.')
                    return redirect(reverse('users:password_change'))
                else:
                    messages.error(request, "Le mot de passe temporaire a expiré. Veuillez demander une réinitialisation de mot de passe.")
                    return redirect(reverse('users:login'))

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


class ForcePasswordChangeView(PasswordChangeView):
    """Vue de changement de mot de passe qui désactive `must_change_password` après succès."""
    template_name = 'users/auth/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

    def form_valid(self, form):
        # Process the password change and clear the must_change_password flag
        response = super().form_valid(form)
        user = self.request.user
        if hasattr(user, 'must_change_password') and user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])

        # If this flow was started after submitting a denunciation, redirect
        # to the incident success page stored in session.
        code = self.request.session.pop('post_submission_incident_code', None)
        # remove the temporary password from session as it is no longer needed
        self.request.session.pop('post_submission_temp_pw', None)
        if code:
            return redirect('core:incident_success', code=code)

        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # expose temporary password (if any) to the template, then keep it until used
        temp = self.request.session.get('post_submission_temp_pw')
        user = getattr(self.request, 'user', None)
        valid = False
        if temp and user and getattr(user, 'temp_password_set_at', None):
            age = timezone.now() - user.temp_password_set_at
            if age <= timedelta(minutes=5):
                valid = True

        if valid:
            ctx['temporary_password'] = temp
        else:
            # expired or missing
            ctx['temporary_password'] = None
            # clear expired session value
            try:
                self.request.session.pop('post_submission_temp_pw')
            except KeyError:
                pass
        return ctx
