# Plateforme de Dénonciation des Incidents de Travail - MEPT-RDC

## Description

Application web sécurisée et professionnelle pour le Ministère de l'Emploi et du Travail de la République Démocratique du Congo. Cette plateforme permet aux travailleurs de dénoncer des incidents liés au travail et aux agents de l'État d'en assurer le suivi.

## Stack Technique

- **Backend**: Django 4.2 (Python)
- **Frontend**: HTML5, CSS pur, JavaScript Vanilla
- **Base de données**: SQLite (développement)
- **Langue**: Français uniquement
- **Design**: Institutionnel, sobre, moderne - Couleur principale : Bleu marine

## Architecture

### Modèles de Données (Étape 1 ✓)

#### 1. **User (Custom User Model)**
- Rôles : Travailleur, Agent, Administrateur
- Relation ManyToMany avec Province (pour les agents)
- Champs : username, email, first_name, last_name, telephone, organisation, etc.

#### 2. **Province**
- Nom et code unique
- Relations inverses : agents, employeurs, incidents

#### 3. **Employeur**
- Champs : nom, secteur d'activité, description
- Localisation : ville, province
- Contact : email, téléphone
- Modifiable par Admin et Agents

#### 4. **Incident (Dénonciation)**
- Code de suivi unique généré automatiquement (format : RDC{année}{uuid_court})
- Relations : Travailleur (nullable), Employeur, Province
- Statuts : Nouvelle, En cours d'analyse, En attente d'informations, Résolue, Classée sans suite
- Types d'incidents : 11 catégories
- Support de l'anonymat complet
- Metadata : dates création/modification/résolution, statut lu/non lu

#### 5. **PieceJointe**
- Formats autorisés : PDF, DOCX, Images, Vidéos, Audios
- Limite : 50 MB par fichier
- Métadonnées : nom, type, taille, date d'ajout

#### 6. **Commentaire**
- Types : Interne (agents seulement), Public (visible au travailleur)
- Auteur, texte, dates création/modification

#### 7. **LogAudit**
- Trail d'audit pour traçabilité complète
- Actions : création, modification statut, assignation, ajout commentaire, etc.

## Configuration du Projet

### Installation

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Initialiser les données (provinces, admin)
python manage.py init_data

# Créer un superuser (optionnel si init_data est utilisé)
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### Accès Admin

- URL : http://localhost:8000/admin/
- Username : admin
- Password : admin123

## Étapes de Développement

### ✅ Étape 1 : Configuration et Modèles
- Architecture complète des données
- Models Django avec relations appropriées
- Admin Django personnalisé avec:
  - Dashboards visuels
  - Filtres intelligents
  - Affichage des statuts en couleur
  - Inlines pour pièces jointes et commentaires

### 📋 Étape 2 : Vues et Logique Métier
- Formulaire de dénonciation public (sans connexion)
- Génération automatique du code de suivi
- Logique de soumission anonyme
- Création de compte/connexion après soumission
- Routes API pour le suivi

### 🎨 Étape 3 : Templates Frontend
- Formulaire public réactif
- Page de succès avec options
- Page de suivi anonyme (par code)
- Authentification (login/register)
- Design responsive avec CSS pur

### 📊 Étape 4 : Dashboards Métier
- Dashboard Admin : vue globale, métriques globales
- Dashboard Agent : vue par province(s), métriques filtrées
- Dashboard Travailleur : suivi de mes incidents
- Tableau détaillé des incidents
- Interface de gestion des tickets

## Guide d'Utilisation des Modèles

### Créer un Utilisateur Travailleur

```python
from core.models import User

travailleur = User.objects.create_user(
    username='jean.doe',
    email='jean@example.cd',
    password='secure_password',
    first_name='Jean',
    last_name='Doe',
    role='travailleur'
)
```

### Créer un Agent avec Provinces Assignées

```python
from core.models import User, Province

agent = User.objects.create_user(
    username='agent.kinshasa',
    email='agent@mept.cd',
    password='secure_password',
    role='agent'
)

# Assigner les provinces
kinshasa = Province.objects.get(nom='Kinshasa')
kasai = Province.objects.get(nom='Kasai')
agent.provinces.add(kinshasa, kasai)
```

### Créer une Dénonciation

```python
from core.models import Incident, Employeur, Province

employeur = Employeur.objects.create(
    nom='Entreprise XYZ',
    secteur='industrie',
    province=kinshasa,
    ville='Kinshasa'
)

incident = Incident.objects.create(
    travailleur=travailleur,
    employeur=employeur,
    province=kinshasa,
    ville='Kinshasa',
    type_incident='salaire',
    description='Employeur n\'a pas payé mon salaire depuis 3 mois',
    est_anonyme=False
)

# Le code de suivi est généré automatiquement
print(f"Code de suivi: {incident.code_suivi}")  # Ex: RDC2024ABC12345
```

### Ajouter une Pièce Jointe

```python
from core.models import PieceJointe
from django.core.files.File import File

with open('preuve.pdf', 'rb') as f:
    piece = PieceJointe.objects.create(
        incident=incident,
        fichier=File(f, name='preuve.pdf'),
        nom_original='preuve.pdf',
        type_fichier='PDF',
        taille_fichier=f.seek(0, 2)  # Get file size
    )
```

### Ajouter un Commentaire

```python
from core.models import Commentaire

# Commentaire interne (agent uniquement)
Commentaire.objects.create(
    incident=incident,
    auteur=agent,
    texte='Dossier en cours d\'analyse. En attente de documents supplémentaires.',
    type_commentaire='interne'
)

# Commentaire public (visible au travailleur)
Commentaire.objects.create(
    incident=incident,
    auteur=agent,
    texte='Nous avons bien reçu votre dénonciation. Un agent traitera votre dossier sous peu.',
    type_commentaire='public'
)
```

## Permissions et Visibilité

### Travailleur
- Peut créer une dénonciation (anonyme ou liée au compte)
- Voit ses propres dénonciations et leurs commentaires publics
- Peut voir le statut avec le code de suivi

### Agent
- Voit les dénonciations des provinces assignées
- Peut modifier le statut des dénonciations
- Peut ajouter des commentaires internes et publics
- Peut assigné du personnel
- Voit les métriques de sa/ses province(s)

### Administrateur
- Vue globale de toutes les dénonciations
- Gestion des comptes utilisateurs
- Gestion de la liste des employeurs
- Gestion des provinces
- Filtrage par toute critère
- Accès complet à l'interface admin

## Fichiers Importants

```
denunciations_app/
├── manage.py
├── requirements.txt
├── README.md
├── denunciations_app/
│   ├── settings.py           # Configuration Django
│   ├── urls.py              # Routes principales
│   ├── wsgi.py
│   └── asgi.py
└── core/
    ├── models.py            # Modèles de données (Étape 1)
    ├── admin.py             # Configuration Admin Django
    ├── views.py             # Vues (Étape 2)
    ├── forms.py             # Formulaires (Étape 2)
    ├── urls.py              # Routes de l'app (Étape 2)
    ├── utils.py             # Fonctions utilitaires
    ├── tests.py             # Tests unitaires
    ├── templates/           # Templates HTML (Étape 3-4)
    │   ├── base.html
    │   ├── form_dénonciation.html
    │   ├── page_succes.html
    │   ├── dashboard_agent.html
    │   └── dashboard_admin.html
    ├── static/
    │   ├── css/
    │   │   ├── style.css    # Styles CSS pur
    │   │   └── dashboard.css
    │   └── js/
    │       ├── main.js      # JavaScript Vanilla
    │       └── dashboard.js
    └── migrations/          # Migrations de base de données
```

## Variables d'Environnement (à créer)

Créer un fichier `.env` à la racine du projet :

```
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
TIME_ZONE=Africa/Kinshasa
```

## Notes de Sécurité

- ✅ Custom User Model pour sécurité renforcée
- ✅ Anonymat complet possible pour les dénonciations
- ✅ Permissions granulaires par rôle
- ✅ Trail d'audit complet (LogAudit)
- ✅ Validation des extensions de fichiers
- ✅ Limite de taille des fichiers
- ⏳ À implémenter : HTTPS, CSRF, authentification 2FA (Étape 2)
- ⏳ À implémenter : Rate limiting, logging avancé (Étape 2+)

## Prochaines Étapes

**Étape 2** : Créer les vues, formulaires et logique de soumission anonyme
**Étape 3** : Développer les templates HTML/CSS pour le formulaire public
**Étape 4** : Implémenter les dashboards avec métriques et drill-down

---

**Version** : 1.0 - Étape 1 ✓  
**Dernière mise à jour** : 2024  
**Licence** : Propriétaire MEPT-RDC
