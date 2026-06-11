"""
Vues personnalisées pour l'administration (gestion des utilisateurs, provinces, entreprises).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods

from users.models import User
from denunciations.models import Province, Employeur
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
    context = {
        'total_users': User.objects.count(),
        'total_agents': User.objects.filter(role='agent').count(),
        'total_travailleurs': User.objects.filter(role='travailleur').count(),
        'total_provinces': Province.objects.count(),
        'total_employeurs': Employeur.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
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
