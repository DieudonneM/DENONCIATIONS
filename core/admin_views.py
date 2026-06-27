"""
Vues personnalisées pour l'administration (gestion des utilisateurs, provinces, entreprises).
"""

import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import ExtractMonth
from django.contrib.auth.forms import PasswordResetForm
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse

from users.models import User
from denunciations.models import Province, Employeur, Incident
from .admin_forms import (
    AdminUserCreateForm, AdminUserEditForm, AdminAgentProvinceForm,
    ProvinceForm, EmployeurForm, UserSearchForm, ProvinceSearchForm, EmployeurSearchForm
)


def admin_required(view_func):
    """Décorateur pour vérifier que l'utilisateur est administrateur."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Accès refusé. Vous devez être connecté en tant qu’administrateur.')
            return redirect('core:home')

        is_admin = getattr(request.user, 'is_administrateur', None)
        if callable(is_admin):
            is_admin = is_admin()
        elif is_admin is None:
            is_admin = request.user.role == 'administrateur' or request.user.is_superuser

        if not is_admin:
            messages.error(request, 'Accès refusé. Vous devez être administrateur.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================================
#                       TABLEAU DE BORD ADMIN
# ============================================================================


def build_filter_url(request, view_name, params=None):
    """Construit une URL de filtre en conservant les filtres actifs actuels."""
    query = request.GET.copy()
    query.pop('page', None)

    if params:
        for key, value in params.items():
            if value in (None, ''):
                query.pop(key, None)
            else:
                query[key] = value

    url = reverse(view_name)
    if query:
        return f'{url}?{query.urlencode()}'
    return url


@login_required
@admin_required
def admin_root(request):
    """Redirige l'URL /admin/ vers le tableau de bord des statistiques."""
    return redirect('core:admin_dashboard')


@login_required
@admin_required
def admin_statistics_dashboard(request):
    """Tableau de bord administrateur affichant les statistiques avec filtres."""
    # Récupérer tous les incidents pour les options de filtre
    all_incidents_for_filters = Incident.objects.all()

    # Appliquer les filtres aux incidents pour les statistiques et graphiques
    incidents_queryset = Incident.objects.select_related('province', 'employeur').all()

    # Paramètres de filtre depuis la requête GET
    current_status_filter = request.GET.get('statut')
    current_province_filter = request.GET.get('province')
    current_sector_filter = request.GET.get('secteur')
    current_type_incident_filter = request.GET.get('type_incident')
    current_est_anonyme_filter = request.GET.get('est_anonyme')
    current_est_lu_filter = request.GET.get('est_lu')

    if current_status_filter:
        incidents_queryset = incidents_queryset.filter(statut=current_status_filter)
    if current_province_filter:
        incidents_queryset = incidents_queryset.filter(province__nom=current_province_filter)
    if current_sector_filter:
        incidents_queryset = incidents_queryset.filter(employeur__secteur=current_sector_filter)
    if current_type_incident_filter:
        incidents_queryset = incidents_queryset.filter(type_incident=current_type_incident_filter)
    if current_est_anonyme_filter:
        incidents_queryset = incidents_queryset.filter(est_anonyme=True if current_est_anonyme_filter == 'true' else False)
    if current_est_lu_filter:
        incidents_queryset = incidents_queryset.filter(est_lu=True if current_est_lu_filter == 'true' else False)

    # Calcul des statistiques basées sur les incidents filtrés
    total_incidents = incidents_queryset.count()
    nouvelle_incidents = incidents_queryset.filter(statut='nouvelle').count()
    analyse_incidents = incidents_queryset.filter(statut='analyse').count()
    attente_incidents = incidents_queryset.filter(statut='attente').count()
    resolue_incidents = incidents_queryset.filter(statut='resolue').count()
    classée_incidents = incidents_queryset.filter(statut='classée').count()
    anonyme_incidents = incidents_queryset.filter(est_anonyme=True).count()
    non_lu_incidents = incidents_queryset.filter(est_lu=False).count()

    stats = {
        'total': total_incidents,
        'nouvelle': nouvelle_incidents,
        'analyse': analyse_incidents,
        'attente': attente_incidents,
        'resolue': resolue_incidents,
        'classée': classée_incidents,
        'anonyme': anonyme_incidents,
        'non_lu': non_lu_incidents,
    }

    type_counts = (
        incidents_queryset
        .values('type_incident')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    province_counts = (
        incidents_queryset
        .values('province__nom')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    sector_counts = (
        incidents_queryset
        .values('employeur__secteur')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )

    province_filters = [
        {
            'label': item['province__nom'] or 'Non spécifiée',
            'filter': item['province__nom'] or 'Non spécifiée',
            'count': item['count'],
            'url': build_filter_url(request, 'core:admin_dashboard', {'province': item['province__nom'] or 'Non spécifiée'}),
        }
        for item in province_counts
    ]
    sector_filters = [
        {
            'label': dict(Employeur.SECTEUR_CHOICES).get(item['employeur__secteur'], 'Autre'),
            'filter': item['employeur__secteur'] or 'autre',
            'count': item['count'],
            'url': build_filter_url(request, 'core:admin_dashboard', {'secteur': item['employeur__secteur'] or 'autre'}),
        }
        for item in sector_counts
    ]
    type_filters = [
        {
            'label': dict(Incident.TYPE_INCIDENT_CHOICES).get(item['type_incident'], 'Autre'),
            'filter': item['type_incident'],
            'count': item['count'],
            'url': build_filter_url(request, 'core:admin_dashboard', {'type_incident': item['type_incident']}),
        }
        for item in type_counts
    ]

    monthly_stats = (
        incidents_queryset
        .annotate(month=ExtractMonth('date_creation'))
        .values('month')
        .annotate(
            total=Count('id'),
            resolved=Count('id', filter=Q(statut='resolue')),
            analysis=Count('id', filter=Q(statut='analyse')),
        )
        .order_by('month')
    )
    month_lookup = {item['month']: item for item in monthly_stats}
    month_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']

    monthly_labels = []
    monthly_total_data = []
    monthly_resolved_data = []
    monthly_analysis_data = []

    now = timezone.now()
    for offset in range(5, -1, -1):
        month_number = ((now.month - offset - 1) % 12) + 1
        year_number = now.year + ((now.month - offset - 1) // 12)
        month_info = month_lookup.get(month_number, {'total': 0, 'resolved': 0, 'analysis': 0})
        monthly_labels.append(f'{month_names[month_number - 1]} {year_number}')
        monthly_total_data.append(month_info['total'])
        monthly_resolved_data.append(month_info['resolved'])
        monthly_analysis_data.append(month_info['analysis'])

    identification_labels = ['Anonymes', 'Identifiés']
    identification_values = [anonyme_incidents, total_incidents - anonyme_incidents]

    status_filter_options = [
        {'label': 'Tous', 'url': build_filter_url(request, 'core:admin_dashboard', {'statut': ''})},
        {'label': 'Nouvelles', 'url': build_filter_url(request, 'core:admin_dashboard', {'statut': 'nouvelle'})},
        {'label': 'Analyse', 'url': build_filter_url(request, 'core:admin_dashboard', {'statut': 'analyse'})},
        {'label': 'En attente', 'url': build_filter_url(request, 'core:admin_dashboard', {'statut': 'attente'})},
        {'label': 'Résolues', 'url': build_filter_url(request, 'core:admin_dashboard', {'statut': 'resolue'})},
        {'label': 'Archivées', 'url': build_filter_url(request, 'core:admin_dashboard', {'statut': 'classée'})},
    ]

    context = {
        'user_name': request.user.get_full_name() or request.user.email,
        'stats': stats,
        'status_filter_options': status_filter_options,
        'reset_filters_url': reverse('core:admin_dashboard'),
        'total_metric_url': build_filter_url(request, 'core:admin_incidents_list', {'statut': ''}),
        'non_lu_metric_url': build_filter_url(request, 'core:admin_incidents_list', {'est_lu': 'false'}),
        'resolved_metric_url': build_filter_url(request, 'core:admin_incidents_list', {'statut': 'resolue'}),
        'pending_metric_url': build_filter_url(request, 'core:admin_incidents_list', {'statut': 'attente'}),
        'archived_metric_url': build_filter_url(request, 'core:admin_incidents_list', {'statut': 'classée'}),
        # Options pour les filtres de la barre latérale
        'all_status_choices': Incident.STATUT_CHOICES,
        'all_provinces': Province.objects.all().order_by('nom'),
        'all_sectors': Employeur.SECTEUR_CHOICES,
        'all_incident_types': Incident.TYPE_INCIDENT_CHOICES,

        # Valeurs des filtres actuellement appliqués
        'current_status_filter': current_status_filter,
        'current_province_filter': current_province_filter,
        'current_sector_filter': current_sector_filter,
        'current_type_incident_filter': current_type_incident_filter,
        'current_est_anonyme_filter': current_est_anonyme_filter,
        'current_est_lu_filter': current_est_lu_filter,

        'province_filters': province_filters,
        'sector_filters': sector_filters,
        'type_filters': type_filters,
        'max_province_count': max((item['count'] for item in province_filters), default=0),
        'max_sector_count': max((item['count'] for item in sector_filters), default=0),
        'max_type_count': max((item['count'] for item in type_filters), default=0),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_total_data': json.dumps(monthly_total_data),
        'monthly_resolved_data': json.dumps(monthly_resolved_data),
        'monthly_analysis_data': json.dumps(monthly_analysis_data),
        'type_chart_labels': json.dumps([item['label'] for item in type_filters]),
        'type_chart_values': json.dumps([item['count'] for item in type_filters]),
        'province_chart_labels': json.dumps([item['label'] for item in province_filters]),
        'province_chart_values': json.dumps([item['count'] for item in province_filters]),
        'sector_chart_labels': json.dumps([item['label'] for item in sector_filters]),
        'sector_chart_values': json.dumps([item['count'] for item in sector_filters]),
        'identification_labels': json.dumps(identification_labels),
        'identification_values': json.dumps(identification_values),
    }
    return render(request, 'core/admin/dashboard.html', context)


@login_required
@admin_required
def admin_global_management(request):
    """Page d'administration globale servant de hub pour les différentes sections de gestion."""
    context = {
        'page_title': 'Administration Globale',
    }
    return render(request, 'core/admin/global_management.html', context)

# ============================================================================
#                       GESTION DES UTILISATEURS
# ============================================================================

@login_required
@admin_required
def admin_users_list(request):
    """Liste des utilisateurs avec recherche et filtrage."""
    users_list = User.objects.all().order_by('-date_joined')
    search_form = UserSearchForm(request.GET or None)
    
    # Recherche
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        role_filter = search_form.cleaned_data.get('role')
        
        if search_query:
            users_list = users_list.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        if role_filter:
            users_list = users_list.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users_list, 20)
    page_number = request.GET.get('page', 1)
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'search_form': search_form,
        'total_count': paginator.count,
    }
    return render(request, 'core/admin/users_list.html', context)


@login_required
@admin_required
def admin_users_create(request):
    """Créer un nouvel utilisateur."""
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Utilisateur {user.email} créé avec succès!')
            return redirect('core:admin_users_list')
    else:
        form = AdminUserCreateForm()
    
    context = {'form': form, 'title': 'Créer un nouvel utilisateur'}
    return render(request, 'core/admin/user_form.html', context)


@login_required
@admin_required
def admin_users_edit(request, user_id):
    """Modifier un utilisateur."""
    user = get_object_or_404(User, pk=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Utilisateur {user.email} modifié avec succès!')
            return redirect('core:admin_users_list')
    else:
        form = AdminUserEditForm(instance=user)
    
    context = {'form': form, 'user': user, 'title': f'Modifier {user.get_full_name()}'}
    return render(request, 'core/admin/user_form.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def admin_users_delete(request, user_id):
    """Supprimer un utilisateur."""
    user = get_object_or_404(User, pk=user_id)
    email = user.email
    user.delete()
    messages.success(request, f'Utilisateur {email} supprimé avec succès!')
    return redirect('core:admin_users_list')


@login_required
@admin_required
@require_http_methods(["POST"])
def admin_users_send_reset_link(request, user_id):
    """
    Envoie un lien de réinitialisation de mot de passe à l'utilisateur.
    Ceci utilise le mécanisme intégré de Django pour plus de sécurité.
    """
    user = get_object_or_404(User, pk=user_id)
    
    form = PasswordResetForm({'email': user.email})
    
    if form.is_valid():
        form.save(
            request=request,
            use_https=request.is_secure(),
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt'
        )
        messages.success(request, f"Un lien de réinitialisation de mot de passe a été envoyé à {user.email}.")
    else:
        messages.error(request, f"Impossible d'envoyer l'email de réinitialisation pour {user.email}. L'utilisateur est-il actif ?")
        
    return redirect('core:admin_users_list')


@login_required
@admin_required
def admin_agents_provinces(request, user_id):
    """Gérer les provinces assignées à un agent."""
    user = get_object_or_404(User, pk=user_id, role='agent')
    
    if request.method == 'POST':
        form = AdminAgentProvinceForm(request.POST, instance=user)
        if form.is_valid():
            selected_provinces = form.cleaned_data.get('provinces') or []
            user.provinces.set(selected_provinces)
            messages.success(request, f'Provinces de {user.get_full_name()} mises à jour!')
            return redirect('core:admin_users_list')
    else:
        form = AdminAgentProvinceForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
        'title': f'Assigner des provinces à {user.get_full_name()}'
    }
    return render(request, 'core/admin/agent_provinces.html', context)


# ============================================================================
#                       GESTION DES PUBLICATIONS
# ============================================================================

@login_required
@admin_required
def admin_incidents_list(request):
    """Liste des publications avec filtre et suppression possible par l'admin."""
    incidents_list = Incident.objects.select_related('employeur', 'province', 'travailleur', 'agent_assigné').order_by('-date_creation')

    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    type_incident = request.GET.get('type_incident', '')
    province_filter = request.GET.get('province', '')
    secteur_filter = request.GET.get('secteur', '')

    if search:
        incidents_list = incidents_list.filter(
            Q(code_suivi__icontains=search) |
            Q(employeur__nom__icontains=search) |
            Q(ville__icontains=search) |
            Q(province__nom__icontains=search)
        )

    if statut:
        incidents_list = incidents_list.filter(statut=statut)

    if type_incident:
        incidents_list = incidents_list.filter(type_incident=type_incident)

    if province_filter:
        incidents_list = incidents_list.filter(province__nom=province_filter)

    if secteur_filter:
        incidents_list = incidents_list.filter(employeur__secteur=secteur_filter)

    est_anonyme = request.GET.get('est_anonyme')
    if est_anonyme in {'1', 'true', 'True', 'yes', 'on'}:
        incidents_list = incidents_list.filter(est_anonyme=True)
    elif est_anonyme in {'0', 'false', 'False', 'no', 'off'}:
        incidents_list = incidents_list.filter(est_anonyme=False)

    est_lu = request.GET.get('est_lu')
    if est_lu in {'1', 'true', 'True', 'yes', 'on'}:
        incidents_list = incidents_list.filter(est_lu=True)
    elif est_lu in {'0', 'false', 'False', 'no', 'off'}:
        incidents_list = incidents_list.filter(est_lu=False)

    paginator = Paginator(incidents_list, 20)
    page_number = request.GET.get('page', 1)
    incidents = paginator.get_page(page_number)

    context = {
        'incidents': incidents,
        'search': search,
        'statut': statut,
        'type_incident': type_incident,
        'province': province_filter,
        'secteur': secteur_filter,
        'total_count': paginator.count,
        'reset_filters_url': reverse('core:admin_incidents_list'),
    }
    return render(request, 'core/admin/incidents_list.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def admin_incidents_delete(request, incident_id):
    """Supprimer une publication depuis l'administration."""
    incident = get_object_or_404(Incident, pk=incident_id)
    code = incident.code_suivi
    incident.delete()
    messages.success(request, f'Publication {code} supprimée avec succès!')
    return redirect('core:admin_incidents_list')


# ============================================================================
#                       GESTION DES PROVINCES
# ============================================================================

@login_required
@admin_required
def admin_provinces_list(request):
    """Liste des provinces avec recherche."""
    provinces_list = Province.objects.all().order_by('nom')
    search_form = ProvinceSearchForm(request.GET or None)
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        if search_query:
            provinces_list = provinces_list.filter(
                Q(nom__icontains=search_query) |
                Q(code__icontains=search_query)
            )
    
    # Pagination
    paginator = Paginator(provinces_list, 25)
    page_number = request.GET.get('page', 1)
    provinces = paginator.get_page(page_number)
    
    context = {
        'provinces': provinces,
        'search_form': search_form,
        'total_count': paginator.count,
    }
    return render(request, 'core/admin/provinces_list.html', context)


@login_required
@admin_required
def admin_provinces_create(request):
    """Créer une nouvelle province."""
    if request.method == 'POST':
        form = ProvinceForm(request.POST)
        if form.is_valid():
            province = form.save()
            messages.success(request, f'Province {province.nom} créée avec succès!')
            return redirect('core:admin_provinces_list')
    else:
        form = ProvinceForm()
    
    context = {'form': form, 'title': 'Créer une nouvelle province'}
    return render(request, 'core/admin/province_form.html', context)


@login_required
@admin_required
def admin_provinces_edit(request, province_id):
    """Modifier une province."""
    province = get_object_or_404(Province, pk=province_id)
    
    if request.method == 'POST':
        form = ProvinceForm(request.POST, instance=province)
        if form.is_valid():
            form.save()
            messages.success(request, f'Province {province.nom} modifiée avec succès!')
            return redirect('core:admin_provinces_list')
    else:
        form = ProvinceForm(instance=province)
    
    context = {'form': form, 'province': province, 'title': f'Modifier {province.nom}'}
    return render(request, 'core/admin/province_form.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def admin_provinces_delete(request, province_id):
    """Supprimer une province."""
    province = get_object_or_404(Province, pk=province_id)
    nom = province.nom
    province.delete()
    messages.success(request, f'Province {nom} supprimée avec succès!')
    return redirect('core:admin_provinces_list')


# ============================================================================
#                       GESTION DES ENTREPRISES
# ============================================================================

@login_required
@admin_required
def admin_employeurs_list(request):
    """Liste des entreprises avec recherche et filtrage."""
    employeurs_list = Employeur.objects.all().order_by('nom')
    search_form = EmployeurSearchForm(request.GET or None)
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        secteur_filter = search_form.cleaned_data.get('secteur')
        
        if search_query:
            employeurs_list = employeurs_list.filter(
                Q(nom__icontains=search_query) |
                Q(ville__icontains=search_query)
            )
        
        if secteur_filter:
            employeurs_list = employeurs_list.filter(secteur=secteur_filter)
    
    # Pagination
    paginator = Paginator(employeurs_list, 25)
    page_number = request.GET.get('page', 1)
    employeurs = paginator.get_page(page_number)
    
    context = {
        'employeurs': employeurs,
        'search_form': search_form,
        'total_count': paginator.count,
    }
    return render(request, 'core/admin/employeurs_list.html', context)


@login_required
@admin_required
def admin_employeurs_create(request):
    """Créer une nouvelle entreprise."""
    if request.method == 'POST':
        form = EmployeurForm(request.POST)
        if form.is_valid():
            employeur = form.save()
            messages.success(request, f'Entreprise {employeur.nom} créée avec succès!')
            return redirect('core:admin_employeurs_list')
    else:
        form = EmployeurForm()
    
    context = {'form': form, 'title': 'Créer une nouvelle entreprise'}
    return render(request, 'core/admin/employeur_form.html', context)


@login_required
@admin_required
def admin_employeurs_edit(request, employeur_id):
    """Modifier une entreprise."""
    employeur = get_object_or_404(Employeur, pk=employeur_id)
    
    if request.method == 'POST':
        form = EmployeurForm(request.POST, instance=employeur)
        if form.is_valid():
            form.save()
            messages.success(request, f'Entreprise {employeur.nom} modifiée avec succès!')
            return redirect('core:admin_employeurs_list')
    else:
        form = EmployeurForm(instance=employeur)
    
    context = {'form': form, 'employeur': employeur, 'title': f'Modifier {employeur.nom}'}
    return render(request, 'core/admin/employeur_form.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def admin_employeurs_delete(request, employeur_id):
    """Supprimer une entreprise."""
    employeur = get_object_or_404(Employeur, pk=employeur_id)
    nom = employeur.nom
    employeur.delete()
    messages.success(request, f'Entreprise {nom} supprimée avec succès!')
    return redirect('core:admin_employeurs_list')
