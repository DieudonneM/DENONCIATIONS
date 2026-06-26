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

# ============================================================================
# DASHBOARDS
# ============================================================================

class DashboardView(LoginRequiredMixin, View):
    """Vue du tableau de bord principal, selon le rôle utilisateur."""
    
    login_url = 'users:login'
    
    def get(self, request):
        """Rediriger vers le dashboard approprié selon le rôle."""
        if user_is_admin(request.user):
            return redirect('core:admin_dashboard')
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
        
        # Incidents visibles par l'agent (maintenant tous les incidents)
        provinces = self.request.user.provinces.all()
        incidents = get_incidents_by_user_role(self.request.user)

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

class EditIncidentView(LoginRequiredMixin, View):
    """Vue pour permettre au dénonciateur de modifier sa publication."""

    template_name = 'core/edit_incident.html'
    login_url = 'users:login'

    def get(self, request, code):
        incident = get_object_or_404(Incident, code_suivi=code)

        if incident.travailleur != request.user:
            return render(request, 'core/error_403.html', status=403)

        form = IncidentForm(
            instance=incident,
            initial={
                'employeur': incident.employeur.nom if incident.employeur else '',
                'autre_type_incident': incident.type_incident_autre,
                'le_fautif': incident.le_fautif,
                'est_anonyme': incident.est_anonyme,
                'email_contact_anonyme': incident.email_contact_anonyme,
                'telephone_contact_anonyme': incident.telephone_contact_anonyme,
            }
        )

        context = {
            'incident': incident,
            'form': form,
            'page_title': 'Modifier votre publication',
        }
        return render(request, self.template_name, context)

    def post(self, request, code):
        incident = get_object_or_404(Incident, code_suivi=code)

        if incident.travailleur != request.user:
            return render(request, 'core/error_403.html', status=403)

        form = IncidentForm(request.POST, request.FILES, instance=incident, initial={
            'employeur': incident.employeur.nom if incident.employeur else '',
            'autre_type_incident': incident.type_incident_autre,
            'le_fautif': incident.le_fautif,
            'est_anonyme': incident.est_anonyme,
            'email_contact_anonyme': incident.email_contact_anonyme,
            'telephone_contact_anonyme': incident.telephone_contact_anonyme,
        })

        if form.is_valid():
            incident = form.save(commit=False)
            incident.travailleur = request.user
            incident.est_anonyme = form.cleaned_data.get('est_anonyme', False)
            incident.save()

            for uploaded_file in request.FILES.getlist('pieces_jointes'):
                PieceJointe.objects.create(
                    incident=incident,
                    fichier=uploaded_file,
                    nom_original=uploaded_file.name,
                    type_fichier=uploaded_file.content_type,
                    taille_fichier=uploaded_file.size,
                )

            messages.success(request, 'Votre publication a été mise à jour avec succès.')
            return redirect('core:incident_detail', code=incident.code_suivi)

        context = {
            'incident': incident,
            'form': form,
            'page_title': 'Modifier votre publication',
        }
        return render(request, self.template_name, context)

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

def mot_ministre(request):
    """Page Mot du Ministre."""
    context = {
        'page_title': 'Mot Du Ministre',
    }
    return render(request, 'core/mot_ministre.html', context)


def textes_legaux(request):
    """Index des textes légaux (liste de sous-pages)."""
    context = {
        'page_title': 'Textes Légaux',
        'legal_items': [
            ('code-du-travail', "Code du travail"),
            ('contrat-de-travail', "Contrat de travail"),
            ('visa-onem', "Visa de l'ONEM"),
            ('reglement-entreprise', "Règlement d'entreprise"),
            ('bulletin-de-paie', "Bulletin de paie"),
        ]
    }
    return render(request, 'core/textes_legaux/index.html', context)


def legal_page(request, slug):
    """Afficher une page légale par slug (placeholder pour l'instant)."""
    allowed = {
        'code-du-travail': 'Code du travail',
        'contrat-de-travail': 'Contrat de travail',
        'visa-onem': "Visa de l'ONEM",
        'reglement-entreprise': "Règlement d'entreprise",
        'bulletin-de-paie': 'Bulletin de paie',
    }

    if slug not in allowed:
        return render(request, 'core/error_404.html', status=404)

    context = {
        'page_title': allowed[slug],
        'slug': slug,
        'title': allowed[slug],
    }

    template_path = f'core/textes_legaux/{slug}.html'
    return render(request, template_path, context)
