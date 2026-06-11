# Carte des Relations entre Modèles

## Diagramme Visual (ASCII)

```
                                ┌─────────────┐
                                │   Province  │
                                └──────┬──────┘
                                       │
                  ┌────────────────┬───┴────┬────────────────┐
                  │                │        │                │
                  ▼                ▼        ▼                ▼
            ┌─────────────┐  ┌───────────┐ │  ┌────────────┐
            │   User      │  │ Employeur ├─┘  │  Incident  │
            │  (Rôles)    │  └───────────┘    └─────┬──────┘
            └──────┬──────┘                          │
                   │                  ┌──────────────┼──────────────┐
                   │                  │              │              │
    ┌──────────────┼──────────────┐   ▼              ▼              ▼
    │              │              │  PieceJointe  Commentaire   LogAudit
    │         Provinces       (Agent only)           │
    │          (ManyToMany)                          │
    │         (pour agents)                     (public/interne)
    │
    └── travailleur = FK(User)
    └── agent = FK(User)

```

## Détail des Relations

### 1. User (Custom User)
```
User
├── 3 rôles : travailleur, agent, administrateur
├── ManyToMany → Province (agents seulement)
├── (inverse) incidents → Incident (travailleur)
├── (inverse) incidents_assignés → Incident (agent)
├── (inverse) commentaires → Commentaire (auteur)
└── (inverse) logs_audit → LogAudit (utilisateur)
```

### 2. Province
```
Province
├── Foreign Keys
├── (inverse) agents → User (ManyToMany)
├── (inverse) employeurs → Employeur
├── (inverse) incidents → Incident
└── Relations
```

### 3. Employeur
```
Employeur
├── Foreign Keys
│   └── province → Province (FK)
└── (inverse) incidents → Incident
```

### 4. Incident (Cœur du système)
```
Incident
├── Foreign Keys
│   ├── travailleur → User (nullable, pour anonymat)
│   ├── employeur → Employeur (mandatory)
│   ├── province → Province (nullable)
│   └── agent_assigné → User (nullable)
└── (inverse)
    ├── pieces_jointes → PieceJointe
    ├── commentaires → Commentaire
    └── logs → LogAudit
```

### 5. PieceJointe
```
PieceJointe
├── Foreign Keys
│   └── incident → Incident (FK)
└── Type MANY-TO-ONE (plusieurs pièces par incident)
```

### 6. Commentaire
```
Commentaire
├── Foreign Keys
│   ├── incident → Incident (FK)
│   └── auteur → User (FK)
├── Type : interne ou public
└── Type MANY-TO-ONE
```

### 7. LogAudit (Traçabilité)
```
LogAudit
├── Foreign Keys
│   ├── incident → Incident (FK)
│   └── utilisateur → User (FK, nullable)
├── Actions tracées : création, modification_statut, assignation, etc.
└── Type MANY-TO-ONE
```

## Requêtes Courantes (ORM Django)

### Obtenir tous les incidents d'une province
```python
from core.models import Province, Incident

province = Province.objects.get(nom='Kinshasa')
incidents = province.incidents.all()
```

### Obtenir tous les incidents d'un agent
```python
from core.models import User

agent = User.objects.get(username='agent1')
incidents = agent.incidents_assignés.all()

# Ou inclure les incidents de ses provinces
incidents = Incident.objects.filter(
    province__in=agent.provinces.all()
)
```

### Obtenir les incidents d'un travailleur
```python
travailleur = User.objects.get(username='travailleur1')
incidents = travailleur.incidents.all()
```

### Obtenir les incidents anonymes
```python
incidents_anonymes = Incident.objects.filter(est_anonyme=True)
```

### Obtenir un incident par code de suivi
```python
incident = Incident.objects.get(code_suivi='RDC2024ABC12345')
```

### Obtenir les commentaires publics d'un incident
```python
commentaires_publics = incident.commentaires.filter(
    type_commentaire='public'
)
```

### Obtenir tous les employeurs d'une province
```python
employeurs = Employeur.objects.filter(province=province)
```

### Obtenir les incidents non lus
```python
incidents_non_lus = Incident.objects.filter(est_lu=False)
```

### Obtenir les statistiques par statut
```python
from django.db.models import Count

stats = Incident.objects.values('statut').annotate(
    count=Count('id')
)

# Résultat:
# [
#   {'statut': 'nouvelle', 'count': 5},
#   {'statut': 'analyse', 'count': 3},
#   {'statut': 'resolue', 'count': 2},
# ]
```

## Dépendances Entre Modèles

```
Ordre de création recommandé:
1. Province (aucune dépendance)
2. User (référence Province via ManyToMany)
3. Employeur (référence Province)
4. Incident (référence User, Employeur, Province)
5. PieceJointe (référence Incident)
6. Commentaire (référence Incident, User)
7. LogAudit (référence Incident, User)
```

## Suppression (Cascade)

```
Suppression de User:
├── Si travailleur : incident.travailleur = NULL
├── Si agent : incident.agent_assigné = NULL
│   et provinces.remove(user)
└── Commentaires : LEFT intact (auteur = NULL)

Suppression de Employeur:
├── CASCADE → supprime tous ses Incidents
└── CASCADE → supprime PieceJointe, Commentaire, LogAudit

Suppression de Province:
├── Employeur.province = NULL
├── Incident.province = NULL
└── User.provinces.remove(province)

Suppression de Incident:
├── CASCADE → supprime PieceJointe
├── CASCADE → supprime Commentaire
└── CASCADE → supprime LogAudit
```

## Indexes (Performance)

```python
# Indexes principaux définis :

Incident:
├── code_suivi (unique, db_index)
├── statut, -date_creation
├── province, statut
└── date_creation (inverse)

LogAudit:
├── incident, -date_creation
└── date_creation (inverse)
```

## Vues Possibles (SQL générées)

### Vue 1: Incidents par Statut et Province
```sql
SELECT 
    core_province.nom,
    core_incident.statut,
    COUNT(*) as count,
    MAX(core_incident.date_creation) as dernier
FROM core_incident
JOIN core_province ON core_incident.province_id = core_province.id
GROUP BY core_province.nom, core_incident.statut
ORDER BY core_province.nom, core_incident.date_creation DESC;
```

### Vue 2: Activité Récente
```sql
SELECT 
    core_incident.code_suivi,
    core_incident.statut,
    core_employeur.nom,
    core_logaudit.action,
    core_logaudit.date_creation
FROM core_logaudit
JOIN core_incident ON core_logaudit.incident_id = core_incident.id
JOIN core_employeur ON core_incident.employeur_id = core_employeur.id
ORDER BY core_logaudit.date_creation DESC
LIMIT 50;
```

## Intégrité des Données

### Contraintes Uniques
- User.username (hérité de AbstractUser)
- Province.nom, Province.code
- Incident.code_suivi
- Employeur.nom, Employeur.province (unique_together)

### Contraintes NOT NULL
- Incident.employeur (mandatory)
- Incident.type_incident
- Incident.description
- Incident.statut (default='nouvelle')
- User.role (default='travailleur')

### Contraintes FK (Cascade/SetNull)
- Incident.travailleur → SET NULL
- Incident.employeur → CASCADE
- Incident.province → SET NULL
- Incident.agent_assigné → SET NULL
- PieceJointe.incident → CASCADE
- Commentaire.incident → CASCADE
- Commentaire.auteur → SET NULL
- LogAudit.incident → CASCADE
- LogAudit.utilisateur → SET NULL

## Statistiques des Modèles

```
Fichiers:
- models.py : ~350 lignes
- admin.py : ~250 lignes
- 7 modèles
- ~40 fields
- ~15 méthodes
- ~20 indexes/contraintes
```

---

**Dernière mise à jour** : Étape 1  
**Prêt pour** : Étape 2 - Implémentation des vues
