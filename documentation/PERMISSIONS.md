# Guide des Permissions et Contrôle d'Accès

## Vue d'ensemble des rôles

### 1. Travailleur
**Description** : Personne qui dénonce un incident de travail.

**Permissions** :
- ✅ Créer une dénonciation (anonyme ou liée au compte)
- ✅ Consulter ses propres dénonciations
- ✅ Lire les commentaires publics sur ses dossiers
- ✅ Voir le statut de ses incidents
- ✅ Voir le code de suivi pour suivi anonyme
- ❌ Modifier le statut d'un incident
- ❌ Voir les commentaires internes
- ❌ Accéder à l'interface admin

### 2. Agent
**Description** : Employé du MEPT chargé de traiter les dénonciations.

**Permissions** :
- ✅ Voir les incidents de sa/ses province(s)
- ✅ Modifier le statut d'un incident
- ✅ Assigner un incident à un agent
- ✅ Ajouter des commentaires internes et publics
- ✅ Voir les pièces jointes
- ✅ Créer une note interne
- ✅ Consulter les métriques de sa/ses province(s)
- ✅ Accéder au dashboard agent
- ❌ Accéder à l'interface admin
- ❌ Voir les incidents d'autres provinces
- ❌ Modifier les informations des employeurs (sauf notes)
- ❌ Gérer les comptes utilisateurs

### 3. Administrateur
**Description** : Gestionnaire système avec accès complet.

**Permissions** :
- ✅ Accès complet à l'interface admin Django
- ✅ Voir tous les incidents
- ✅ Gérer les comptes utilisateurs
- ✅ Gérer la liste des employeurs
- ✅ Gérer les provinces
- ✅ Consulter les logs d'audit
- ✅ Créer/modifier des agents et leurs assignations
- ✅ Filtrer par tous les critères
- ✅ Exporter les données
- ✅ Accéder au dashboard complet

## Implémentation des Contrôles d'Accès

### Utilisation de décorateurs (Étape 2)

```python
from django.contrib.auth.decorators import login_required
from core.auth_backends import user_is_agent, user_is_admin

@login_required
def agent_dashboard(request):
    if not user_is_agent(request.user):
        return redirect('403')
    # ...

@login_required
def admin_dashboard(request):
    if not user_is_admin(request.user):
        return redirect('403')
    # ...
```

### Utilisation de Mixins (Étape 2)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from core.auth_backends import user_is_agent

class AgentDashboardView(LoginRequiredMixin, View):
    login_url = 'login'
    
    def dispatch(self, request, *args, **kwargs):
        if not user_is_agent(request.user):
            return redirect('403')
        return super().dispatch(request, *args, **kwargs)
```

### Filtrage des QuerySets

```python
from core.utils import get_incidents_by_user_role

def dashboard(request):
    incidents = get_incidents_by_user_role(request.user)
    # incidents sera filtré selon le rôle automatiquement
```

## Anonymat et Confidentialité

### Dénonciation Anonyme
- L'incident est créé SANS travailleur lié (`travailleur=None`)
- Un code de suivi unique est généré
- L'utilisateur peut consulter l'incident avec ce code (pas de connexion requise)
- L'agent ne verra jamais l'identité du dénonçant

### Dénonciation Liée
- L'incident est créé avec le travailleur lié
- Le travailleur doit se connecter pour voir ses incidents
- L'agent ne verra toujours pas l'identité du dénonçant (MASQUÉE)
- Seuls les commentaires publics sont visibles au travailleur

### Masquage de l'Identité

```python
# Dans le modèle Incident
est_anonyme = models.BooleanField(default=True)

# Dans les vues (Étape 2)
def get_incident_for_agent(incident):
    # Retourner les données SANS l'identité du travailleur
    return {
        'code_suivi': incident.code_suivi,
        'employeur': incident.employeur,
        'type_incident': incident.type_incident,
        # ... mais PAS travailleur.name
    }
```

## Audit Trail (LogAudit)

Toutes les actions importantes sont enregistrées :
- Création d'incident
- Modification de statut
- Assignation d'agent
- Ajout de commentaire
- Ajout de pièce jointe
- Résolution

Accessible uniquement aux administrateurs.

## Prochaines Étapes (Étape 2)

- [ ] Implémenter les décorateurs et mixins
- [ ] Créer les vues avec contrôles d'accès
- [ ] Tester les permissions par rôle
- [ ] Valider l'anonymat
- [ ] Implémenter la pagination et filtrage
- [ ] Ajouter la gestion des erreurs 403/404
