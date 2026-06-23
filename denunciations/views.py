"""
Vues pour l'application denunciations.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages

from .models import Incident, Commentaire, Province, Employeur, PieceJointe
from .forms import IncidentForm, CommentaireForm, SearchIncidentForm, FilterIncidentForm
from users.models import User
from users.auth_backends import user_is_agent, user_is_admin
import openpyxl
from openpyxl.utils import get_column_letter
from django.http import HttpResponse


# ============================================================================
# VUES PUBLIQUES (Sans authentification requise)
# ============================================================================

class IncidentPublicFormView(View):
    """Vue pour créer une dénonciation publiquement (sans connexion)."""
    
    template_name = 'denunciations/form_denonciation.html'
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
            return redirect('denunciations:incident_success', code=incident.code_suivi)
        
        context = {
            'form': form,
            'page_title': 'Dénoncer un incident de travail',
            'provinces': Province.objects.all(),
            'employeurs': Employeur.objects.all(),
        }
        return render(request, self.template_name, context)


class IncidentSuccessView(TemplateView):
    """Page de succès après création d'une dénonciation."""
    
    template_name = 'denunciations/page_succes.html'
    
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
    
    template_name = 'denunciations/search_denonciation.html'
    
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
                return render(request, 'denunciations/detail_denonciation_public.html', context)
            
            except Incident.DoesNotExist:
                form.add_error(None, 'Code de suivi introuvable.')
        
        context = {
            'form': form,
            'page_title': 'Consulter une dénonciation',
        }
        return render(request, self.template_name, context)


# ============================================================================
# VUES DÉTAIL DES INCIDENTS (Authentifiées)
# ============================================================================

class IncidentDetailView(LoginRequiredMixin, View):
    """Vue détaillée d'un incident."""
    
    template_name = 'denunciations/detail_incident.html'
    login_url = 'users:login'
    
    def get(self, request, code):
        """Afficher les détails d'un incident."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions
        if not self._can_view_incident(request.user, incident):
            context = {'error': 'Vous n\'avez pas accès à cette dénonciation.'}
            return render(request, 'core/error_403.html', context, status=403)
        
        # Marquer comme lu si c'est un agent
        if user_is_agent(request.user) and not incident.est_lu:
            incident.est_lu = True
            incident.save()
        
        # Récupérer les commentaires
        if request.user.role == 'travailleur':
            commentaires = incident.commentaires.filter(type_commentaire='public')
        else:
            commentaires = incident.commentaires.all()
        
        context = {
            'incident': incident,
            'commentaires': commentaires,
            'pieces_jointes': incident.pieces_jointes.all(),
            'form': CommentaireForm() if user_is_agent(request.user) else None,
            'user_is_agent': user_is_agent(request.user),
            'user_is_admin': user_is_admin(request.user),
            'user_can_comment': user_is_agent(request.user),
            'page_title': f'Détails - {incident.code_suivi}',
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, code):
        """Ajouter un commentaire (agents seulement)."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions
        if not user_is_agent(request.user):
            return render(request, 'core/error_403.html', status=403)
        
        form = CommentaireForm(request.POST)
        
        if form.is_valid():
            commentaire = form.save(commit=False)
            commentaire.incident = incident
            commentaire.auteur = request.user
            # Rendre visible automatiquement les commentaires publiés par un agent
            if user_is_agent(request.user):
                commentaire.type_commentaire = 'public'
            commentaire.save()
            
            messages.success(request, 'Commentaire ajouté avec succès.')
            return redirect('denunciations:incident_detail', code=code)
        
        context = {
            'incident': incident,
            'form': form,
        }
        
        return render(request, self.template_name, context)


class ToggleCommentVisibility(LoginRequiredMixin, View):
    """Basculer la visibilité d'un commentaire (public <-> interne)."""
    login_url = 'users:login'

    def post(self, request, comment_id):
        try:
            commentaire = Commentaire.objects.get(id=comment_id)
        except Commentaire.DoesNotExist:
            return JsonResponse({'error': 'Commentaire introuvable'}, status=404)

        # Autorisation : agents et admins seulement
        if not (user_is_agent(request.user) or user_is_admin(request.user)):
            return JsonResponse({'error': 'Permission refusée'}, status=403)

        commentaire.type_commentaire = 'public' if commentaire.type_commentaire == 'interne' else 'interne'
        commentaire.save()

        messages.success(request, 'Visibilité du commentaire modifiée.')
        return redirect(request.META.get('HTTP_REFERER', '/'))


class ExportIncidentsExcel(LoginRequiredMixin, View):
    """Exporter une liste d'incidents (filtrée) au format Excel."""
    login_url = 'users:login'

    def get(self, request):
        # Filtrer selon paramètres GET simples
        qs = Incident.objects.all().select_related('employeur', 'province')
        statut = request.GET.get('statut')
        ttype = request.GET.get('type_incident')
        search = request.GET.get('search')
        if statut:
            qs = qs.filter(statut=statut)
        if ttype:
            qs = qs.filter(type_incident=ttype)
        if search:
            qs = qs.filter(
                Q(code_suivi__icontains=search) |
                Q(employeur__nom__icontains=search) |
                Q(ville__icontains=search)
            )

        # Créer workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Incidents'

        headers = ['Code', 'Type', 'Employeur', 'Ville', 'Province', 'Statut', 'Date création', 'Description', 'Le fautif']
        ws.append(headers)

        for inc in qs.order_by('-date_creation'):
            ws.append([
                inc.code_suivi,
                inc.get_type_incident_display(),
                inc.employeur.nom if inc.employeur else '',
                inc.ville,
                inc.province.nom if inc.province else '',
                inc.get_statut_display(),
                inc.date_creation.strftime('%Y-%m-%d %H:%M'),
                inc.description,
                getattr(inc, 'le_fautif', '') or ''
            ])

        # Ajuster largeur colonnes
        for i, col in enumerate(ws.columns, 1):
            max_length = 0
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[get_column_letter(i)].width = min(50, max_length + 2)

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=incidents_export.xlsx'
        wb.save(response)
        return response


class ExportIncidentExcel(LoginRequiredMixin, View):
    """Exporter un incident unique (détails + commentaires) en Excel."""
    login_url = 'users:login'

    def get(self, request, code):
        incident = get_object_or_404(Incident, code_suivi=code)

        # Vérifier permission de visualiser
        if not IncidentDetailView._can_view_incident(request.user, incident):
            return render(request, 'core/error_403.html', status=403)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Incident'

        # Détails incident
        rows = [
            ('Code', incident.code_suivi),
            ('Type', incident.get_type_incident_display()),
            ('Employeur', incident.employeur.nom if incident.employeur else ''),
            ('Ville', incident.ville),
            ('Province', incident.province.nom if incident.province else ''),
            ('Statut', incident.get_statut_display()),
            ('Date création', incident.date_creation.strftime('%Y-%m-%d %H:%M')),
            ('Description', incident.description),
            ('Le fautif', getattr(incident, 'le_fautif', '') or ''),
            ('Pièces jointes', ', '.join([p.fichier.name for p in incident.pieces_jointes.all()])),
        ]

        for key, val in rows:
            ws.append([key, val])

        # Comments sheet
        ws2 = wb.create_sheet(title='Commentaires')
        ws2.append(['Auteur', 'Type', 'Date', 'Texte'])
        for c in incident.commentaires.all().order_by('date_creation'):
            ws2.append([str(c.auteur) if c.auteur else 'Anonyme', c.type_commentaire, c.date_creation.strftime('%Y-%m-%d %H:%M'), c.texte])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=incident_{incident.code_suivi}.xlsx'
        wb.save(response)
        return response
    
    @staticmethod
    def _can_view_incident(user, incident):
        """Vérifier si l'utilisateur peut voir l'incident."""
        if user_is_admin(user):
            return True
        
        if user_is_agent(user):
            return incident.province in user.provinces.all()
        
        if user.role == 'travailleur':
            return incident.travailleur == user
        
        return False


class UpdateIncidentStatusView(LoginRequiredMixin, View):
    """Vue pour modifier le statut d'un incident."""
    
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
        return redirect('denunciations:incident_detail', code=code)


class AssignIncidentView(LoginRequiredMixin, View):
    """Vue pour assigner un incident à un agent."""
    
    login_url = 'users:login'
    
    def post(self, request, code):
        """Assigner l'incident."""
        incident = get_object_or_404(Incident, code_suivi=code)
        
        # Vérifier les permissions (admin seulement)
        if not user_is_admin(request.user):
            return JsonResponse({'error': 'Permission refusée'}, status=403)
        
        agent_id = request.POST.get('agent_id')
        
        try:
            agent = User.objects.get(id=agent_id, role='agent')
            incident.agent_assigné = agent
            incident.save()
            
            messages.success(request, f'Incident assigné à {agent.get_full_name()}.')
        except User.DoesNotExist:
            messages.error(request, 'Agent introuvable.')
        
        return redirect('denunciations:incident_detail', code=code)
