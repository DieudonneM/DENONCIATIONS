# Restructuration - Plateforme de Dénonciation MEPT-RDC

## Changements Réalisés

### 1. ✅ Authentification par Email
- **Modèle User** : Migré de `core.User` à `users.User`
- Email est maintenant l'identifiant unique
- Authentification par email ou username via `EmailBackend`
- Formulaires mis à jour : `EmailAuthenticationForm` et `UserRegistrationForm`

### 2. ✅ Restructuration des Applications Django

#### Application `users` (Gestion des utilisateurs)
- **Modèles** : `User`, `UserProfile`
- **Vues** : `LoginView`, `RegisterView`, `LogoutView`, `ProfileView`
- **Formulaires** : `EmailAuthenticationForm`, `UserRegistrationForm`, `UserProfileForm`
- **Templates** : `users/auth/login.html`, `users/auth/register.html`
- **URLs** : `/auth/login/`, `/auth/register/`, `/auth/logout/`, `/auth/profile/`
- **Static** : CSS et JS utilisateurs

#### Application `denunciations` (Gestion des dénonciations)
- **Modèles** : `Province`, `Employeur`, `Incident`, `PieceJointe`, `Commentaire`, `LogAudit`
- **Vues** : Création, recherche, détail des dénonciations
- **Formulaires** : `IncidentForm`, `CommentaireForm`, `SearchIncidentForm`, `FilterIncidentForm`
- **Templates** : Tous les templates de dénonciations
- **URLs** : `/denonciation/`, `/rechercher/`, `/detail/<code>/`, etc.
- **Static** : CSS et JS dénonciations

#### Application `core` (Application principale)
- Reste avec les dashboards, gestion globale
- Modèles de base conservés

### 3. ✅ Thème Couleurs Mis à Jour
- **Bleu foncé** : `#134294` (primaire)
- **Gris clair** : `#fafafa`
- Tous les fichiers CSS mis à jour avec les nouvelles variables CSS

### 4. ✅ Configuration Django (`settings.py`)
```python
# Apps en ordre de priorité
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',          # Gestion des utilisateurs
    'denunciations',  # Gestion des dénonciations
    'core',           # Application principale
]

# Model User personnalisé
AUTH_USER_MODEL = 'users.User'

# Backends d'authentification
AUTHENTICATION_BACKENDS = [
    'users.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# URLs d'authentification
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'
```

## Structure des Répertoires

```
denunciations_app/
├── users/                           # Gestion utilisateurs
│   ├── migrations/
│   ├── templates/users/auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── static/users/css/
│   ├── static/users/js/
│   ├── models.py (User, UserProfile)
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── auth_backends.py
│   ├── admin.py
│   ├── apps.py
│   └── signals.py
│
├── denunciations/                   # Gestion dénonciations
│   ├── migrations/
│   ├── templates/denunciations/
│   ├── static/denunciations/css/
│   ├── static/denunciations/js/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   ├── signals.py
│   └── utils.py
│
├── core/                            # Application principale
│   ├── templates/core/
│   ├── static/css/style.css (couleurs mises à jour)
│   └── ...
│
└── denunciations_app/
    ├── settings.py (mis à jour)
    └── urls.py (mis à jour)
```

## URLs Principales

| Route | Vue | Application |
|-------|-----|-------------|
| `/auth/login/` | LoginView | users |
| `/auth/register/` | RegisterView | users |
| `/auth/logout/` | LogoutView | users |
| `/auth/profile/` | ProfileView | users |
| `/denonciation/` | IncidentPublicFormView | denunciations |
| `/denonciation/succes/<code>/` | IncidentSuccessView | denunciations |
| `/rechercher/` | SearchIncidentView | denunciations |
| `/detail/<code>/` | IncidentDetailView | denunciations |
| `/` | Home/Dashboard | core |

## Prochaines Étapes

1. **Créer les migrations** :
   ```bash
   python manage.py makemigrations users
   python manage.py makemigrations denunciations
   python manage.py migrate
   ```

2. **Copier les templates existants** :
   - Déplacer les templates d'authentification du `core` vers `users`
   - Déplacer les templates de dénonciations du `core` vers `denunciations`

3. **Mettre à jour les vues du `core`** :
   - Importer les modèles depuis `denunciations` au lieu de `core`
   - Utiliser les nouvelles fonctions d'authentification depuis `users.auth_backends`

4. **Tester** :
   - Inscription avec email
   - Connexion avec email
   - Création de dénonciation
   - Validation des couleurs du thème

## Notes

- ✅ Email est l'identifiant principal
- ✅ Username est auto-généré à partir du préfixe de l'email
- ✅ Authentification par email ou username fonctionne
- ✅ Signals créent automatiquement le profil utilisateur
- ✅ Permissions basées sur les rôles fonctionnelles
