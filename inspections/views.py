from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import ListView, View
from django.views.generic.edit import CreateView

from users.auth_backends import user_is_staff

from .forms import OrdreDeMissionForm
from .models import Entreprise, Etablissement, OrdreDeMission
from .pdf import build_ordre_de_mission_pdf


class InspectionStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Reserve les missions d'inspection aux agents et administrateurs."""

    login_url = 'users:login'

    def test_func(self):
        return user_is_staff(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "Vous n'avez pas acces aux missions d'inspection.")
            return redirect('core:dashboard')
        return super().handle_no_permission()


def _collision_queryset(mission):
    """Retourne les missions pouvant entrer en conflit avec la mission proposee."""
    missions = OrdreDeMission.objects.filter(entreprise=mission.entreprise).exclude(pk=mission.pk)
    same_target = Q(scope='NATIONAL')
    if mission.scope == 'NATIONAL':
        same_target |= Q(scope='LOCAL')
    elif mission.etablissement_id:
        same_target |= Q(scope='LOCAL', etablissement=mission.etablissement)
    else:
        return OrdreDeMission.objects.none()

    active_overlap = Q(
        statut__in=('PROGRAMME', 'EN_COURS'),
        date_debut__lte=mission.date_fin,
        date_fin__gte=mission.date_debut,
    )
    cooling_off = Q(
        statut='FINALISE',
        date_fin__gte=timezone.localdate() - timedelta(days=90),
    )
    return missions.filter(same_target).filter(active_overlap | cooling_off)


def _conflict_details(mission):
    conflict = _collision_queryset(mission).order_by('-date_fin', '-created_at').first()
    if not conflict:
        return ''

    entity_labels = {
        'CABINET': 'Cabinet du Ministre',
        'IGT': "l'IGT",
        'PROVINCIALE': "l'Inspection Provinciale du Travail",
    }
    target = 'cette entreprise' if conflict.scope == 'NATIONAL' else f'ce site ({conflict.etablissement.nom_site})'
    return (
        f"Une mission de {entity_labels[conflict.entite_emetteure]} est deja "
        f"{conflict.get_statut_display().lower()} sur {target} du "
        f"{conflict.date_debut:%d/%m/%Y} au {conflict.date_fin:%d/%m/%Y}."
    )


class MissionCreateView(InspectionStaffRequiredMixin, CreateView):
    model = OrdreDeMission
    form_class = OrdreDeMissionForm
    template_name = 'inspections/soumettre_mission.html'
    success_url = reverse_lazy('inspections:soumettre_mission')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if form.instance.check_collision() and not form.cleaned_data.get('derogation_justification'):
            form.add_error(
                'derogation_justification',
                'Une justification de derogation est obligatoire en cas de collision.',
            )
            return self.form_invalid(form)

        response = super().form_valid(form)
        messages.success(self.request, f"L'ordre de mission {self.object.numero_om} a ete emis.")
        return response

    def get_success_url(self):
        return f"{reverse('inspections:soumettre_mission')}?mission={self.object.pk}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mission_id = self.request.GET.get('mission')
        if mission_id and mission_id.isdigit():
            context['created_mission'] = OrdreDeMission.objects.filter(pk=mission_id).first()
        return context


class OrdreDeMissionPdfView(InspectionStaffRequiredMixin, View):
    """Exporte un ordre de mission au format PDF."""

    def get(self, request, pk):
        mission = get_object_or_404(OrdreDeMission, pk=pk)
        response = HttpResponse(build_ordre_de_mission_pdf(mission), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{mission.numero_om}.pdf"'
        return response


class OrdreDeMissionListView(InspectionStaffRequiredMixin, ListView):
    """Liste filtrable des ordres de mission emis."""

    model = OrdreDeMission
    template_name = 'inspections/liste_ordres_mission.html'
    context_object_name = 'missions'
    paginate_by = 20

    def get_queryset(self):
        queryset = OrdreDeMission.objects.select_related('entreprise', 'etablissement', 'created_by')
        query = self.request.GET.get('q', '').strip()
        entite = self.request.GET.get('entite_emetteure')
        scope = self.request.GET.get('scope')
        statut = self.request.GET.get('statut')

        if query:
            queryset = queryset.filter(
                Q(numero_om__icontains=query) |
                Q(entreprise__nom__icontains=query) |
                Q(etablissement__nom_site__icontains=query)
            )
        if entite in dict(OrdreDeMission.ENTITE_CHOICES):
            queryset = queryset.filter(entite_emetteure=entite)
        if scope in dict(OrdreDeMission.SCOPE_CHOICES):
            queryset = queryset.filter(scope=scope)
        if statut in dict(OrdreDeMission.STATUT_CHOICES):
            queryset = queryset.filter(statut=statut)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context.update({
            'entite_choices': OrdreDeMission.ENTITE_CHOICES,
            'scope_choices': OrdreDeMission.SCOPE_CHOICES,
            'statut_choices': OrdreDeMission.STATUT_CHOICES,
            'query_string': query_params.urlencode(),
        })
        return context


@require_GET
def search_entreprises_api(request):
    """Retourne les suggestions d'entreprises pour le champ de recherche."""
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentification requise.'}, status=401)
    if not user_is_staff(request.user):
        return JsonResponse({'detail': 'Acces reserve aux agents et administrateurs.'}, status=403)

    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    companies = Entreprise.objects.filter(nom__icontains=query).order_by('nom')[:10]
    return JsonResponse({
        'results': [
            {
                'id': company.pk,
                'nom': company.nom,
                'rccm': company.rccm,
                'nif': company.nif,
            }
            for company in companies
        ]
    })


@require_GET
def check_collision_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentification requise.'}, status=401)
    if not user_is_staff(request.user):
        return JsonResponse({'detail': 'Acces reserve aux agents et administrateurs.'}, status=403)

    entreprise_id = request.GET.get('entreprise_id')
    etablissement_id = request.GET.get('etablissement_id') or None
    scope = request.GET.get('scope')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if not all((entreprise_id, scope, date_debut, date_fin)):
        return JsonResponse({'detail': 'Parametres incomplets.'}, status=400)

    form = OrdreDeMissionForm({
        'entite_emetteure': 'IGT',
        'scope': scope,
        'entreprise': entreprise_id,
        'etablissement': etablissement_id,
        'objet_mission': 'Verification de collision',
        'date_debut': date_debut,
        'date_fin': date_fin,
    })
    if not form.is_valid():
        return JsonResponse({'detail': 'Parametres invalides.', 'errors': form.errors}, status=400)

    mission = form.save(commit=False)
    has_collision = mission.check_collision()
    return JsonResponse({
        'has_collision': has_collision,
        'conflict_details': _conflict_details(mission) if has_collision else '',
        'requires_derogation': has_collision,
    })


def _staff_api_error(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentification requise.'}, status=401)
    if not user_is_staff(request.user):
        return JsonResponse({'detail': 'Acces reserve aux agents et administrateurs.'}, status=403)
    return None


@require_GET
def search_etablissements_api(request):
    """Retourne les sites connus pour l'entreprise selectionnee."""
    error_response = _staff_api_error(request)
    if error_response:
        return error_response

    entreprise_id = request.GET.get('entreprise_id')
    query = request.GET.get('q', '').strip()
    if not entreprise_id or len(query) < 2:
        return JsonResponse({'results': []})

    sites = Etablissement.objects.filter(
        entreprise_id=entreprise_id,
        nom_site__icontains=query,
    ).order_by('nom_site')[:10]
    return JsonResponse({'results': [
        {
            'id': site.pk,
            'nom_site': site.nom_site,
            'province': site.get_province_display(),
            'ville_territoire': site.ville_territoire,
        }
        for site in sites
    ]})


@require_POST
def create_etablissement_api(request):
    """Cree un site puis le renvoie afin de le selectionner dans la mission."""
    error_response = _staff_api_error(request)
    if error_response:
        return error_response

    entreprise_id = request.POST.get('entreprise_id')
    nom_site = request.POST.get('nom_site', '').strip()
    province = request.POST.get('province', '').strip()
    ville_territoire = request.POST.get('ville_territoire', '').strip()
    adresse = request.POST.get('adresse', '').strip()
    if not all((entreprise_id, nom_site, province, ville_territoire)):
        return JsonResponse({'detail': 'Le nom, la province et la ville ou territoire sont obligatoires.'}, status=400)
    if province not in dict(Etablissement.PROVINCE_CHOICES):
        return JsonResponse({'detail': 'Province invalide.'}, status=400)

    entreprise = get_object_or_404(Entreprise, pk=entreprise_id)
    etablissement, created = Etablissement.objects.get_or_create(
        entreprise=entreprise,
        nom_site__iexact=nom_site,
        defaults={
            'nom_site': nom_site,
            'province': province,
            'ville_territoire': ville_territoire,
            'adresse': adresse,
        },
    )
    return JsonResponse({
        'id': etablissement.pk,
        'nom_site': etablissement.nom_site,
        'province': etablissement.get_province_display(),
        'ville_territoire': etablissement.ville_territoire,
        'created': created,
    }, status=201 if created else 200)