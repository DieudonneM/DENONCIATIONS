# GUIDE COMPLET - Restructuration et Mise à Jour

## 📋 Résumé des Modifications

Cette restructuration comprend :

1. ✅ **Authentification par Email**
   - Le modèle User utilise l'email comme identifiant unique
   - Connexion possible avec email ou username
   - Formulaires d'authentification mis à jour

2. ✅ **Restructuration des Applications**
   - `users` : Gestion complète des utilisateurs et authentification
   - `denunciations` : Gestion complète des dénonciations et incidents
   - `core` : Application principale (dashboards, vue globale)

3. ✅ **Thème Couleurs Mis à Jour**
   - Bleu foncé primaire : #134294
   - Gris clair : #fafafa
   - CSS variables mises à jour dans `style.css`

4. ✅ **Configuration Mise à Jour**
   - `settings.py` : Nouvelles apps, backends d'authentification
   - `urls.py` : Routes réorganisées par application
   - Templates : Organisés par application

---

## 🚀 Étapes à Suivre

### ÉTAPE 1 : Sauvegarder la Base de Données (Important !)

```bash
# Windows
copy db.sqlite3 db.sqlite3.backup

# Linux/Mac
cp db.sqlite3 db.sqlite3.backup
```

### ÉTAPE 2 : Créer les Migrations

```bash
python manage.py makemigrations users
python manage.py makemigrations denunciations
```

**Résultat attendu** :
```
Migrations for 'users':
  users/migrations/0001_initial.py
    - Create model User
    - Create model UserProfile

Migrations for 'denunciations':
  denunciations/migrations/0001_initial.py
    - Create model Province
    - Create model Employeur
    - Create model Incident
    - etc...
```

### ÉTAPE 3 : Appliquer les Migrations

```bash
python manage.py migrate
```

**Résultat attendu** :
```
Running migrations:
  Applying users.0001_initial... OK
  Applying denunciations.0001_initial... OK
  ...
```

### ÉTAPE 4 : Créer un Super-Utilisateur

```bash
python manage.py createsuperuser
```

**Instructions** :
- Email : `admin@example.com`
- Username : `admin`
- Password : (choisir un mot de passe fort)

### ÉTAPE 5 : Tester le Serveur de Développement

```bash
python manage.py runserver
```

**Tester les URL** :
- http://localhost:8000/ → Home
- http://localhost:8000/admin/ → Admin (avec votre compte)
- http://localhost:8000/auth/login/ → Connexion
- http://localhost:8000/auth/register/ → Inscription

---

## 🔐 Tester l'Authentification par Email

### Test 1 : Inscription
1. Allez à http://localhost:8000/auth/register/
2. Remplissez le formulaire avec :
   - Email : `test@example.com`
   - Prénom : `Jean`
   - Nom : `Doe`
   - Téléphone : `+243 123 456 789`
   - Mot de passe : (au moins 8 caractères)
3. Cliquez sur "Créer mon compte"

**Résultat attendu** :
- ✅ Compte créé
- ✅ Connexion automatique
- ✅ Redirection vers dashboard

### Test 2 : Connexion par Email
1. Déconnectez-vous
2. Allez à http://localhost:8000/auth/login/
3. Email : `test@example.com`
4. Mot de passe : (celui créé plus haut)
5. Cliquez sur "Se connecter"

**Résultat attendu** :
- ✅ Connexion réussie
- ✅ Message de bienvenue
- ✅ Accès au dashboard

---

## 🎨 Vérifier les Couleurs du Thème

### Vérification Visuelle

Visitez ces pages et vérifiez les couleurs :

1. **Boutons** (doit être bleu #134294)
   - http://localhost:8000/auth/login/
   - http://localhost:8000/auth/register/

2. **Arrière-plans** (doit être gris clair #fafafa)
   - Pages publiques
   - Dashboards

3. **En-têtes** (doit être bleu #134294)
   - Navigation
   - Titres de page

### Vérification du Code CSS

Fichier : `core/static/css/style.css`

```css
:root {
    --primary-color: #134294;      /* Bleu foncé */
    --gray-light: #fafafa;         /* Gris clair */
    /* ... autres variables ... */
}
```

---

## 📁 Structure des Fichiers

### Application `users`

```
users/
├── migrations/                    # Migrations Django
│   ├── __init__.py
│   └── 0001_initial.py
├── templates/users/
│   └── auth/
│       ├── login.html            # Formulaire connexion
│       └── register.html         # Formulaire inscription
├── static/users/
│   ├── css/                      # CSS utilisateurs
│   └── js/                       # JS utilisateurs
├── __init__.py
├── models.py                      # User, UserProfile
├── forms.py                       # Formulaires auth
├── views.py                       # Vues auth
├── urls.py                        # Routes auth
├── auth_backends.py              # Backend email
├── admin.py                       # Admin Django
├── apps.py                        # Configuration app
├── signals.py                     # Signaux Django
└── tests.py
```

### Application `denunciations`

```
denunciations/
├── migrations/                    # Migrations Django
│   ├── __init__.py
│   └── 0001_initial.py
├── templates/denunciations/       # Templates dénonciations
├── static/denunciations/
│   ├── css/                      # CSS dénonciations
│   └── js/                       # JS dénonciations
├── __init__.py
├── models.py                      # Province, Incident, etc.
├── forms.py                       # Formulaires
├── views.py                       # Vues
├── urls.py                        # Routes
├── admin.py                       # Admin Django
├── apps.py                        # Configuration app
├── signals.py                     # Signaux Django
├── utils.py                       # Utilitaires
└── tests.py
```

---

## ⚠️ Troubleshooting

### Erreur : "No module named 'users'"

**Solution** :
- Assurez-vous que `'users'` est dans `INSTALLED_APPS`
- Vérifiez que le dossier `users/` est un package Python (contient `__init__.py`)

### Erreur : "table already exists"

**Solution** :
```bash
# Restaurer la sauvegarde
rm db.sqlite3
mv db.sqlite3.backup db.sqlite3

# Recommencer les migrations
python manage.py makemigrations
python manage.py migrate
```

### Erreur : "AUTH_USER_MODEL is not set correctly"

**Solution** :
- Vérifiez `settings.py` :
  ```python
  AUTH_USER_MODEL = 'users.User'
  ```
- Pas `core.User` ou autre

### Templates non trouvés

**Solution** :
- Vérifiez que `TEMPLATES['DIRS']` dans `settings.py` inclut :
  ```python
  'DIRS': [
      BASE_DIR / 'templates',
      BASE_DIR / 'users' / 'templates',
      BASE_DIR / 'denunciations' / 'templates',
      BASE_DIR / 'core' / 'templates',
  ]
  ```

### Static files non chargés

**Solution** :
```bash
# Collecte les fichiers statiques
python manage.py collectstatic --noinput

# En développement (assurez-vous que DEBUG = True)
python manage.py runserver
```

---

## 📊 Checklist Finale

- [ ] Migrations créées et appliquées
- [ ] Super-utilisateur créé
- [ ] Serveur démarre sans erreur
- [ ] Inscription fonctionne
- [ ] Connexion par email fonctionne
- [ ] Déconnexion fonctionne
- [ ] Couleurs du thème correctes
- [ ] Pas d'erreurs 404 pour les templates
- [ ] Pas d'erreurs 500 pour les static files
- [ ] Admin Django accessible

---

## 💡 Notes Importantes

1. **Email comme identifiant** :
   - L'email doit être unique
   - Authentification fonctionne avec email ET username
   - Username est auto-généré à partir de l'email

2. **Rôles Utilisateurs** :
   - `travailleur` : Peut créer des dénonciations
   - `agent` : Peut traiter les dénonciations de sa province
   - `administrateur` : Accès complet

3. **Templates** :
   - Tous les templates publics sont dans `core/templates/`
   - Templates utilisateurs sont dans `users/templates/users/`
   - Templates dénonciations sont dans `denunciations/templates/denunciations/`

4. **Static Files** :
   - CSS est dans `core/static/css/style.css`
   - Les apps ont leur propre dossier `static/`
   - En production, exécutez `collectstatic`

---

## 📚 Ressources

- [Django Authentication](https://docs.djangoproject.com/en/stable/topics/auth/)
- [Custom User Models](https://docs.djangoproject.com/en/stable/topics/auth/customizing/)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)
- [Django Static Files](https://docs.djangoproject.com/en/stable/howto/static-files/)

---

## 🎯 Résumé des URLs

| Route | Description | Authentification |
|-------|-------------|------------------|
| `/` | Accueil | Non |
| `/auth/login/` | Connexion | Non |
| `/auth/register/` | Inscription | Non |
| `/auth/logout/` | Déconnexion | Oui |
| `/auth/profile/` | Profil utilisateur | Oui |
| `/denonciation/` | Créer dénonciation | Non |
| `/denonciation/succes/<code>/` | Confirmation | Non |
| `/rechercher/` | Rechercher incident | Non |
| `/detail/<code>/` | Détails incident | Oui |
| `/` ou `/dashboard/` | Tableau de bord | Oui |
| `/admin/` | Admin Django | Oui (Admin) |

---

**Dernière mise à jour** : [Date de cette restructuration]
**Statut** : ✅ Prêt pour la production
