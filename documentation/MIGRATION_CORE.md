# 📚 GUIDE DE MIGRATION DU CODE `core` VERS LES NOUVELLES APPS

## Vue d'Ensemble

Après la restructuration, vous devez mettre à jour le code existant dans `core` pour utiliser les nouveaux modèles et fonctions des apps `users` et `denunciations`.

---

## 🔄 Migration des Imports

### Avant (Ancien Code dans `core`)

```python
# core/views.py
from core.models import User, Incident, Province, Employeur
from core.forms import UserLoginForm, UserRegistrationForm
from core.auth_backends import user_is_agent, user_is_admin
```

### Après (Code Migré)

```python
# core/views.py
from users.models import User
from denunciations.models import Incident, Province, Employeur
from users.forms import EmailAuthenticationForm, UserRegistrationForm
from users.auth_backends import user_is_agent, user_is_admin
```

---

## 🎯 Changements Requis dans `core/urls.py`

### Routes d'Authentification

**Avant** :
```python
path('auth/login/', views.UserLoginView.as_view(), name='login'),
path('auth/register/', views.UserRegisterView.as_view(), name='register'),
path('auth/logout/', views.logout_view, name='logout'),
```

**Après** (Rediriger vers `users` app) :
```python
# Remplacer les routes d'auth par des redirects
from django.views.generic import RedirectView

path('auth/login/', RedirectView.as_view(url='users:login'), name='login'),
path('auth/register/', RedirectView.as_view(url='users:register'), name='register'),
path('auth/logout/', RedirectView.as_view(url='users:logout'), name='logout'),
```

Ou inclure directement les URLs :
```python
from django.urls import include

urlpatterns = [
    # ... autres routes ...
    path('auth/', include('users.urls')),
    path('', include('denunciations.urls')),
]
```

---

## 🛠️ Changements dans `core/views.py`

### Import des Modèles

```python
# Remplacer
from core.models import User, Incident, Province, Employeur, Commentaire, PieceJointe

# Par
from users.models import User
from denunciations.models import (
    Incident, Province, Employeur, Commentaire, PieceJointe
)
```

### Import des Formulaires

```python
# Remplacer
from core.forms import (
    UserLoginForm, UserRegistrationForm, IncidentForm, 
    CommentaireForm, SearchIncidentForm, FilterIncidentForm
)

# Par
from users.forms import EmailAuthenticationForm, UserRegistrationForm, UserProfileForm
from denunciations.forms import (
    IncidentForm, CommentaireForm, SearchIncidentForm, FilterIncidentForm
)
```

### Import des Backends

```python
# Remplacer
from core.auth_backends import user_is_agent, user_is_admin

# Par
from users.auth_backends import user_is_agent, user_is_admin
```

### Supprimer les Vues d'Authentification du `core`

Si vous utilisez les URLs redirectes, les vues d'auth du `core` ne sont plus nécessaires.

```python
# Supprimer les vues suivantes de core/views.py :
# - UserLoginView
# - UserRegisterView
# - logout_view
# - ProfileView (si elle existe)
```

---

## 🔌 Changements dans `core/models.py`

### Supprimer le Modèle User

```python
# SUPPRIMER cette classe de core/models.py
class User(AbstractUser):
    """Custom User Model avec 3 rôles : Travailleur, Agent, Administrateur."""
    # ... tout le code ...
```

### Importer User depuis `users`

Si vous en avez besoin dans `core` :

```python
from django.contrib.auth import get_user_model
User = get_user_model()  # Récupère 'users.User'

# Ou directement
from users.models import User
```

### Supprimer les Modèles de Dénonciations

```python
# SUPPRIMER de core/models.py :
# - Province
# - Employeur
# - Incident
# - PieceJointe
# - Commentaire
# - LogAudit
```

Ces modèles sont maintenant dans `denunciations/models.py`

---

## 📝 Changements dans `core/admin.py`

### Avant

```python
from core.models import User, Province, Incident, Employeur, Commentaire, PieceJointe

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # ...

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    # ...
```

### Après

Vous pouvez supprimer complètement les admin des modèles migrés. Ils sont maintenant dans :
- `users/admin.py` → Admin pour User
- `denunciations/admin.py` → Admin pour Incident, Province, etc.

**`core/admin.py` ne doit contenir QUE les admin de core** (s'il en existe)

```python
# core/admin.py peut être vidé ou contenir
# uniquement les admin de l'app core

# Les admins migrés sont maintenant dans :
# - users/admin.py
# - denunciations/admin.py
```

---

## 🔧 Changements dans `core/forms.py`

### Supprimer les Formulaires Migrés

```python
# SUPPRIMER de core/forms.py :
# - UserLoginForm (ou AuthenticationForm)
# - UserRegistrationForm
# - IncidentForm
# - CommentaireForm
# - SearchIncidentForm
# - FilterIncidentForm
```

### Ajouter une Note

```python
"""
Formulaires pour l'application core.

Note: Les formulaires d'authentification sont maintenant dans :
- users/forms.py

Les formulaires de dénonciations sont maintenant dans :
- denunciations/forms.py

Ce fichier contient les formulaires spécifiques à core uniquement.
"""
```

---

## 🔐 Changements dans `core/auth_backends.py`

### Supprimer ou Vider le Fichier

Le fichier `core/auth_backends.py` peut être supprimé. Il y a maintenant `users/auth_backends.py`

Si vous avez du code custom, déplacez-le dans `users/auth_backends.py`

---

## 📊 Changements dans `core/migrations/`

### ⚠️ Important

**NE SUPPRIMEZ PAS les migrations existantes de `core`!**

Les migrations de `core` doivent rester pour l'historique, même si les modèles ont changé.

### Supprimer les Modèles des Migrations

Si vous avez modifié `core/models.py` pour supprimer les modèles :

1. **Créer une nouvelle migration** :
```bash
python manage.py makemigrations core
```

2. **Ne le faites QUE si les modèles supprimés ont été migrés aux autres apps d'abord!**

3. **Appliquer les migrations** :
```bash
python manage.py migrate core
```

---

## 📁 Plan de Migration Complet

### Étape 1 : Préparer les Nouvelles Apps

✅ **DÉJÀ FAIT** :
- ✅ Créer `users/` avec tous les fichiers
- ✅ Créer `denunciations/` avec tous les fichiers
- ✅ Mettre à jour `settings.py`

### Étape 2 : Mettre à Jour `core`

À faire :

1. **Mettre à jour `core/views.py`** :
   - Remplacer les imports
   - Supprimer les vues d'auth (ou rediriger)

2. **Mettre à jour `core/models.py`** :
   - Supprimer les modèles migrés
   - Garder les modèles spécifiques à `core`

3. **Mettre à jour `core/forms.py`** :
   - Supprimer les formulaires migrés

4. **Mettre à jour `core/urls.py`** :
   - Remplacer les routes d'auth
   - Inclure les URLs des nouvelles apps

5. **Mettre à jour `core/admin.py`** :
   - Supprimer les admin des modèles migrés

6. **Mettre à jour `core/tests.py`** :
   - Mettre à jour les imports de tests

### Étape 3 : Exécuter les Migrations

```bash
# Créer les migrations
python manage.py makemigrations users
python manage.py makemigrations denunciations
python manage.py makemigrations core

# Appliquer les migrations
python manage.py migrate
```

---

## 🔗 Template Links

### Avant (Ancien)

```html
{% url 'core:login' %}
{% url 'core:register' %}
{% url 'core:logout' %}
{% url 'core:incident_form' %}
```

### Après (Nouveau)

```html
{% url 'users:login' %}
{% url 'users:register' %}
{% url 'users:logout' %}
{% url 'denunciations:incident_form' %}
```

---

## 🎯 Checklist de Migration

- [ ] Mettre à jour les imports de `core/views.py`
- [ ] Supprimer les vues d'auth du `core`
- [ ] Supprimer les modèles migrés de `core/models.py`
- [ ] Supprimer les formulaires migrés de `core/forms.py`
- [ ] Mettre à jour les routes de `core/urls.py`
- [ ] Mettre à jour `core/admin.py`
- [ ] Mettre à jour les templates
- [ ] Exécuter les migrations
- [ ] Tester l'application
- [ ] Supprimer les fichiers obsolètes de `core`

---

## 💡 Conseils

1. **Faites une sauvegarde** avant de commencer
2. **Testez en développement** d'abord
3. **Lisez les erreurs** Django (elles guident généralement vers la solution)
4. **Exécutez les tests** après les modifications
5. **Vérifiez les templates** pour les URL obsolètes

---

## 🚀 Après la Migration

Une fois tout fait :

1. Supprimez les fichiers obsolètes de `core/` :
   - `core/models.py` (garder uniquement les modèles de core)
   - `core/forms.py` (garder uniquement les formulaires de core)
   - `core/auth_backends.py` (supprimer - il y a maintenant `users/auth_backends.py`)

2. Exécutez les tests :
```bash
python manage.py test
```

3. Lancez le serveur :
```bash
python manage.py runserver
```

---

**Note** : Cette migration est progressive. Vous pouvez le faire étape par étape sans casser l'application si vous testé après chaque changement.
