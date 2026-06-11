"""
Vues Django pour l'application de dénonciation.

Contient :
- Formulaire public de dénonciation
- Page de succès avec code de suivi
- Suivi anonyme par code
- Authentification (login/register)
- Dashboards Agent et Admin
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from users.models import User
from .models import Province, Employeur
from denunciations.models import Incident, Commentaire, PieceJointe
from .forms import (
    IncidentForm, CommentaireForm, SearchIncidentForm, FilterIncidentForm
)
from .utils import (
    generate_tracking_code, get_incidents_by_user_role,
    get_incident_statistics_by_user, check_user_can_view_incident
)
from .auth_backends import user_is_agent, user_is_admin, user_is_travailleur


# ============================================================================
# VUES PUBLIQUES (Sans authentification requise)
# ============================================================================

class IncidentPublicFormView(View):
    """Vue pour créer une dénonciation publiquement (sans connexion)."""
    
    template_name = 'core/form_denonciation.html'
    form_class = IncidentForm
    
    def get(self, request):
        """Afficher le formulaire vide."""
        form = self.form_class()
        context = {
            'form': form,
            'page_title': 'Dénoncer un incident de travail',
            'provinces': Province.objects.all(),
            'employeurs': Employeur.objects.all(),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Traiter la soumission du formulaire."""
        form = self.form_class(request.POST, request.FILES)
        
        if form.is_valid():
            # Créer l'incident
            incident = form.save(commit=False)
            incident.statut = 'nouvelle'
            incident.est_lu = False
            
            # Gérer l'anonymat
            if form.cleaned_data.get('est_anonyme'):
                incident.travailleur = None
            
            incident.save()
            
            # Gérer les fichiers joints
            files = request.FILES.getlist('pieces_jointes')
            for file in files:
                PieceJointe.objects.create(
                    incident=incident,
                    fichier=file,
                    nom_original=file.name,
                    type_fichier=file.content_type,
                    taille_fichier=file.size,
                )
            
            # Rediriger vers la page de succès
            return redirect('core:incident_success', code=incident.code_suivi)
        
        context = {
            'form': form,
            'page_title': 'Dénoncer un incident de travail',
            'provinces': Province.objects.all(),
            'employeurs': Employeur.objects.all(),
        }
        return render(request, self.template_name, context)


class IncidentSuccessView(TemplateView):
    """Page de succès après création d'une dénonciation."""
    
    template_name = 'core/page_succes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code = kwargs.get('code')
        
        try:
            incident = Incident.objects.get(code_suivi=code)
            context['incident'] = incident
            context['code_suivi'] = code
            context['type_incident'] = incident.get_type_incident_display()
            context['employeur'] = incident.employeur.nom
        except Incident.DoesNotExist:
            context['error'] = 'Dénonciation non trouvée.'
        
        return context


class SearchIncidentView(View):
    """Vue pour rechercher et consulter un incident par code de suivi (anonyme)."""
    
    template_name = 'core/search_denonciation.html'
    
    def get(self, request):
        """Afficher le formulaire de recherche."""
        form = SearchIncidentForm()
        context = {
            'form': form,
            'page_title': 'Consulter une dénonciation',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Rechercher et afficher le résultat."""
        form = SearchIncidentForm(request.POST)
        
        if form.is_valid():
            code = form.cleaned_data['code_suivi']
            
            try:
                incident = Incident.objects.get(code_suivi=code)
                
                # Marquer comme lu
                if not incident.est_lu:
                    incident.est_lu = True
                    incident.save()
                
                context = {
                    'incident': incident,
                    'code_suivi': code,
                    'commentaires_publics': incident.commentaires.filter(type_commentaire='public'),
                    'pieces_jointes': incident.pieces_jointes.all(),
                }
                return render(request, 'core/detail_denonciation_public.html', context)
            
            except Incident.DoesNotExist:
                form.add_error(None, 'Code de suivi introuvable.')
        
        context = {
            'form': form,
            'page_title': 'Consulter une dénonciation',
        }
        return render(request, self.template_name, context)


# ============================================================================
# DASHBOARDS
# ============================================================================

class DashboardView(LoginRequiredMixin, View):
    """Vue du tableau de bord (redirects selon le rôle)."""
    
    login_url = 'users:login'
    
    def get(self, request):
        """Rediriger vers le dashboard approprié selon le rôle."""
        if user_is_admin(request.user):
            return redirect('core:dashboard_admin')
        elif user_is_agent(request.user):
            return redirect('core:dashboard_agent')
        else:
            return redirect('core:dashboard_travailleur')


class DashboardAdminView(LoginRequiredMixin, TemplateView):
    """Dashboard administrateur (vue globale)."""
    
    template_name = 'core/dashboard_admin.html'
    login_url = 'users:login'
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifier que c'est un admin."""
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not user_is_admin(request.user):
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        incidents = Incident.objects.all()
        
        context['stats'] = {
            'total': incidents.count(),
            'nouvelle': incidents.filter(statut='nouvelle').count(),
            'analyse': incidents.filter(statut='analyse').count(),
            'attente': incidents.filter(statut='attente').count(),
            'resolue': incidents.filter(statut='resolue').count(),
            'classée': incidents.filter(statut='classée').count(),
            'anonyme': incidents.filter(est_anonyme=True).count(),
            'non_lu': incidents.filter(est_lu=False).count(),
        }
        
        # Statistiques par province
        context['stats_by_province'] = (
            incidents.values('province__nom')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Statistiques par type d'incident
        context['stats_by_type'] = (
            incidents.values('type_incident')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Gestion des utilisateurs
        context['total_agents'] = User.objects.filter(role='agent').count()
        context['total_travailleurs'] = User.objects.filter(role='travailleur').count()
        context['total_users'] = User.objects.count()
        context['recent_agents'] = User.objects.filter(role='agent').order_by('-date_joined')[:5]
        
        # Gestion des provinces et entreprises
        context['total_provinces'] = Province.objects.count()
        context['total_employeurs'] = Employeur.objects.count()
        context['recent_provinces'] = Province.objects.order_by('-date_creation')[:5]
        context['recent_employeurs'] = Employeur.objects.order_by('-date_creation')[:5]
        
        # Incidents récents
        context['recent_incidents'] = incidents.order_by('-date_creation')[:10]
        
        # Filtrage optionnel
        filter_form = FilterIncidentForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        if filter_form.is_valid():
            queryset = incidents
            
            if filter_form.cleaned_data.get('statut'):
                queryset = queryset.filter(statut=filter_form.cleaned_data['statut'])
            
            if filter_form.cleaned_data.get('type_incident'):
                queryset = queryset.filter(type_incident=filter_form.cleaned_data['type_incident'])
            
            if filter_form.cleaned_data.get('search'):
                search = filter_form.cleaned_data['search']
                queryset = queryset.filter(
                    Q(code_suivi__icontains=search) |
                    Q(employeur__nom__icontains=search) |
                    Q(ville__icontains=search)
                )
            
            context['filtered_incidents'] = queryset[:20]
        
        return context


class DashboardAgentView(LoginRequiredMixin, TemplateView):
    """Dashboard agent (vue par province)."""
    
    template_name = 'core/dashboard_agent.html'
    login_url = 'users:login'
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifier que c'est un agent."""
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not user_is_agent(request.user):
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Incidents de la province de l'agent
        provinces = self.request.user.provinces.all()
        incidents = Incident.objects.filter(province__in=provinces)
        
        context['provinces'] = provinces
        context['stats'] = {
            'total': incidents.count(),
            'nouvelle': incidents.filter(statut='nouvelle').count(),
            'analyse': incidents.filter(statut='analyse').count(),
            'attente': incidents.filter(statut='attente').count(),
            'resolue': incidents.filter(statut='resolue').count(),
            'classée': incidents.filter(statut='classée').count(),
            'non_lu': incidents.filter(est_lu=False).count(),
            'anonyme': incidents.filter(est_anonyme=True).count(),
        }
        
        # Incidents assignés à cet agent
        context['my_incidents'] = incidents.filter(agent_assigné=self.request.user).order_by('-date_creation')[:10]
        
        # Incidents non assignés
        context['unassigned_incidents'] = incidents.filter(agent_assigné__isnull=True).order_by('-date_creation')[:10]
        
        # Incidents récents
        context['recent_incidents'] = incidents.order_by('-date_creation')[:10]
        
        # Gestion des provinces et entreprises
        context['provinces_count'] = provinces.count()
        context['assigned_provinces'] = provinces.order_by('nom')
        context['employeurs_in_provinces'] = (
            Employeur.objects.filter(province__in=provinces.values_list('id', flat=True))
            .select_related('province')
            .distinct()
            .order_by('nom')
        )
        context['recent_employeurs'] = list(context['employeurs_in_provinces'][:8])
        context['total_employeurs'] = context['employeurs_in_provinces'].count()
        
        # Filtrage
        filter_form = FilterIncidentForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        return context


class DashboardTravailleurView(LoginRequiredMixin, TemplateView):
    """Dashboard travailleur (ses propres dénonciations)."""
    
    template_name = 'core/dashboard_travailleur.html'
    login_url = 'users:login'
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifier que c'est un travailleur."""
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not user_is_travailleur(request.user):
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Incidents du travailleur
        incidents = Incident.objects.filter(travailleur=self.request.user)
        
        context['stats'] = {
            'total': incidents.count(),
            'nouvelle': incidents.filter(statut='nouvelle').count(),
            'analyse': incidents.filter(statut='analyse').count(),
            'attente': incidents.filter(statut='attente').count(),
            'resolue': incidents.filter(statut='resolue').count(),
            'classée': incidents.filter(statut='classée').count(),
        }
        
        context['incidents'] = incidents.order_by('-date_creation')
        
        return context


# ============================================================================
# VUES DÉTAIL DES INCIDENTS
# ============================================================================

class IncidentDetailView(LoginRequiredMixin, View):
    """Vue détaillée d'un incident."""
    
    template_name = 'core/detail_incident.html'
    login_url = 'users:login'
    
    def get(self, request, code):
        """Afficher les détails d'un incident."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions
        if not check_user_can_view_incident(request.user, incident):
            return render(request, 'core/error_403.html', status=403)
        
        # Marquer comme lu si c'est un agent
        if user_is_agent(request.user) and not incident.est_lu:
            incident.est_lu = True
            incident.save()
        
        # Récupérer les commentaires (publics pour travailleur, tous pour agent/admin)
        if request.user.role == 'travailleur':
            commentaires = incident.commentaires.filter(type_commentaire='public')
        else:
            commentaires = incident.commentaires.all()
        
        available_agents = []
        if user_is_admin(request.user) and incident.province:
            available_agents = User.objects.filter(
                role='agent',
                is_active=True,
                provinces=incident.province
            ).distinct().order_by('first_name', 'last_name', 'id')

        context = {
            'incident': incident,
            'commentaires': commentaires,
            'pieces_jointes': incident.pieces_jointes.all(),
            'form': CommentaireForm() if (user_is_agent(request.user) or user_is_admin(request.user)) else None,
            'available_agents': available_agents,
            'user_can_edit': user_is_agent(request.user) or user_is_admin(request.user),
            'user_is_admin': user_is_admin(request.user),
            'user_can_comment': user_is_agent(request.user) or user_is_admin(request.user),
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, code):
        """Ajouter un commentaire (agents seulement)."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions
        if not (user_is_agent(request.user) or user_is_admin(request.user)):
            return render(request, 'core/error_403.html', status=403)
        
        form = CommentaireForm(request.POST)
        
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.incident = incident
            commentaire.auteur = request.user
            commentaire.save()
            
            messages.success(request, 'Commentaire ajouté avec succès.')
            return redirect('core:incident_detail', code=code)
        
        available_agents = []
        if user_is_admin(request.user) and incident.province:
            available_agents = User.objects.filter(
                role='agent',
                is_active=True,
                provinces=incident.province
            ).distinct().order_by('first_name', 'last_name', 'id')

        context = {
            'incident': incident,
            'form': form,
            'available_agents': available_agents,
            'user_can_edit': user_is_agent(request.user) or user_is_admin(request.user),
            'user_is_admin': user_is_admin(request.user),
            'user_can_comment': user_is_agent(request.user) or user_is_admin(request.user),
        }
        
        return render(request, self.template_name, context)


class UpdateIncidentStatusView(LoginRequiredMixin, View):
    """Vue pour modifier le statut d'un incident (agents/admins)."""
    
    login_url = 'users:login'
    
    def post(self, request, code):
        """Modifier le statut."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions
        if not (user_is_agent(request.user) or user_is_admin(request.user)):
            return JsonResponse({'error': 'Permission refusée'}, status=403)
        
        new_status = request.POST.get('statut')
        
        if new_status not in dict(Incident.STATUT_CHOICES):
            return JsonResponse({'error': 'Statut invalide'}, status=400)
        
        old_status = incident.statut
        incident.statut = new_status
        
        if new_status == 'resolue':
            incident.date_resolution = timezone.now()
        
        incident.save()
        
        messages.success(request, f'Statut changé de {old_status} à {new_status}.')
        return redirect('core:incident_detail', code=code)


class AssignIncidentView(LoginRequiredMixin, View):
    """Vue pour assigner un incident à un agent."""
    
    login_url = 'users:login'
    
    def post(self, request, code):
        """Assigner l'incident."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions (admin seulement)
        if not user_is_admin(request.user):
            return JsonResponse({'error': 'Permission refusée'}, status=403)
        
        agent_id = request.POST.get('agent')
        
        if not agent_id:
            messages.error(request, 'Veuillez sélectionner un agent.')
            return redirect('core:incident_detail', code=code)

        try:
            agent = User.objects.get(id=agent_id, role='agent')
            incident.agent_assigné = agent
            incident.save()
            
            messages.success(request, f'Incident assigné à {agent.get_full_name()}.')
        except User.DoesNotExist:
            messages.error(request, 'Agent non trouvé.')
        
        return redirect('core:incident_detail', code=code)


# ============================================================================
# PAGES STATIQUES
# ============================================================================

def home_view(request):
    """Page d'accueil."""
    context = {
        'page_title': 'Accueil',
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    """Page À propos."""
    context = {
        'page_title': 'À propos',
    }
    return render(request, 'core/about.html', context)


def contact_view(request):
    """Page Contact."""
    context = {
        'page_title': 'Contact',
    }
    return render(request, 'core/contact.html', context)
