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
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods

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

@login_required
@admin_required
def admin_root(request):
    """Redirige l'URL /admin/ vers le tableau de bord administrateur personnalisé."""
    return redirect('core:admin_dashboard')


@login_required
@admin_required
def admin_dashboard(request):
    """Tableau de bord administrateur personnalisé."""
    incidents = Incident.objects.select_related('province').all()
    stats = {
        'total': incidents.count(),
        'nouvelle': incidents.filter(statut='nouvelle').count(),
        'analyse': incidents.filter(statut='analyse').count(),
        'attente': incidents.filter(statut='attente').count(),
        'resolue': incidents.filter(statut='resolue').count(),
        'classée': incidents.filter(statut='classée').count(),
        'anonyme': incidents.filter(est_anonyme=True).count(),
        'non_lu': incidents.filter(est_lu=False).count(),
    }

    type_counts = (
        incidents
        .values('type_incident')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    province_counts = (
        incidents
        .values('province__nom')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    sector_counts = (
        incidents
        .values('employeur__secteur')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )
    monthly_total_counts = (
        incidents
        .annotate(month=ExtractMonth('date_creation'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_resolved_counts = (
        incidents
        .filter(statut='resolue')
        .annotate(month=ExtractMonth('date_creation'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_analysis_counts = (
        incidents
        .filter(statut='analyse')
        .annotate(month=ExtractMonth('date_creation'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    monthly_labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    monthly_total_data = [0] * 12
    monthly_resolved_data = [0] * 12
    monthly_analysis_data = [0] * 12

    for item in monthly_total_counts:
        monthly_total_data[item['month'] - 1] = item['count']
    for item in monthly_resolved_counts:
        monthly_resolved_data[item['month'] - 1] = item['count']
    for item in monthly_analysis_counts:
        monthly_analysis_data[item['month'] - 1] = item['count']

    identification_data = [
        {'label': 'Anonymes', 'value': stats['anonyme']},
        {'label': 'Identifiés', 'value': max(stats['total'] - stats['anonyme'], 0)},
    ]

    context = {
        'user_name': request.user.get_full_name() or request.user.email,
        'stats': stats,
        'status_cards': [
            {'label': 'Total', 'value': stats['total'], 'filter': '', 'color': '#1E40AF'},
            {'label': 'Résolu', 'value': stats['resolue'], 'filter': 'statut=resolue', 'color': '#16A34A'},
            {'label': 'Non lue', 'value': stats['non_lu'], 'filter': 'est_lu=0', 'color': '#DC2626'},
            {'label': 'En analyse', 'value': stats['analyse'], 'filter': 'statut=analyse', 'color': '#4338CA'},
            {'label': 'Classée', 'value': stats['classée'], 'filter': 'statut=classée', 'color': '#374151'},
        ],
        'type_chart_labels': json.dumps([dict(Incident.TYPE_INCIDENT_CHOICES).get(item['type_incident'], 'Autre') for item in type_counts]),
        'type_chart_values': json.dumps([item['count'] for item in type_counts]),
        'province_chart_labels': json.dumps([item['province__nom'] or 'Non spécifiée' for item in province_counts]),
        'province_chart_values': json.dumps([item['count'] for item in province_counts]),
        'province_filters': [
            {'label': item['province__nom'] or 'Non spécifiée', 'filter': item['province__nom'] or 'Non spécifiée'}
            for item in province_counts
        ],
        'sector_filters': [
            {'label': item['employeur__secteur'] or 'Autre', 'filter': item['employeur__secteur'] or 'autre'}
            for item in sector_counts
        ],
        'type_filters': [
            {'label': dict(Incident.TYPE_INCIDENT_CHOICES).get(item['type_incident'], 'Autre'), 'filter': item['type_incident']}
            for item in type_counts
        ],
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_total_data': json.dumps(monthly_total_data),
        'monthly_resolved_data': json.dumps(monthly_resolved_data),
        'monthly_analysis_data': json.dumps(monthly_analysis_data),
        'identification_labels': json.dumps([entry['label'] for entry in identification_data]),
        'identification_values': json.dumps([entry['value'] for entry in identification_data]),
    }
    return render(request, 'core/admin/dashboard.html', context)


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
def admin_users_reset_password(request, user_id):
    """Réinitialiser le mot de passe d'un utilisateur avec un mot de passe par défaut."""
    user = get_object_or_404(User, pk=user_id)
    new_password = 'ChangeMe123!'
    user.set_password(new_password)
    user.save(update_fields=['password'])
    messages.success(request, f'Mot de passe réinitialisé pour {user.email}. Nouveau mot de passe : {new_password}')
    return redirect('core:admin_users_list')


@login_required
@admin_required
@require_http_methods(["POST"])
def admin_users_refresh_password(request, user_id):
    """Générer un nouveau mot de passe aléatoire pour un utilisateur."""
    user = get_object_or_404(User, pk=user_id)
    new_password = get_random_string(length=12)
    user.set_password(new_password)
    user.save(update_fields=['password'])
    messages.success(request, f'Nouveau mot de passe généré pour {user.email}. Mot de passe : {new_password}')
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
        'total_count': paginator.count,
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
