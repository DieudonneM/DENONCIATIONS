# 🚀 COMMENCER APRÈS LA RESTRUCTURATION

## ⚡ Démarrage Rapide

### Option 1 : Utiliser le Script Automatique (Recommandé)

```bash
# Exécuter le script de setup
python setup_restructuring.py
```

**Ce script fera** :
- ✅ Créer les migrations pour `users`
- ✅ Créer les migrations pour `denunciations`
- ✅ Appliquer toutes les migrations
- ✅ Afficher les prochaines étapes

### Option 2 : Étapes Manuelles

```bash
# 1. Créer les migrations
python manage.py makemigrations users
python manage.py makemigrations denunciations

# 2. Appliquer les migrations
python manage.py migrate

# 3. Créer un superutilisateur
python manage.py createsuperuser

# 4. Lancer le serveur
python manage.py runserver
```

---

## 📍 Après la Configuration

### 1️⃣ Créer un Compte Administrateur

Si vous n'en avez pas déjà un :

```bash
python manage.py createsuperuser
```

**Exemple** :
```
Email : admin@example.com
Username : admin
Password : (tapez votre mot de passe)
Password (again) : (confirmez)
```

### 2️⃣ Accéder à l'Admin Django

```bash
python manage.py runserver
```

Allez à : http://localhost:8000/admin/

Connectez-vous avec votre compte administrateur.

### 3️⃣ Tester l'Authentification par Email

#### Test d'Inscription

1. Allez à http://localhost:8000/auth/register/
2. Remplissez le formulaire :
   - Email : `test@example.com`
   - Prénom : `Jean`
   - Nom : `Dupont`
   - Téléphone : `+243 123 456 789`
   - Mot de passe : `SecurePassword123`
3. Cliquez sur "Créer mon compte"

#### Test de Connexion

1. Déconnectez-vous (http://localhost:8000/auth/logout/)
2. Allez à http://localhost:8000/auth/login/
3. Email : `test@example.com`
4. Mot de passe : `SecurePassword123`
5. Cliquez sur "Se connecter"

✅ Vous devriez être connecté !

### 4️⃣ Vérifier les Couleurs du Thème

Visitez ces pages et vérifiez les couleurs :

- **Bleu foncé #134294** : Boutons, en-têtes, navigation
- **Gris clair #fafafa** : Arrière-plans

Pages à vérifier :
- http://localhost:8000/auth/login/
- http://localhost:8000/auth/register/
- http://localhost:8000/admin/

### 5️⃣ Créer une Dénonciation (Test)

1. Allez à http://localhost:8000/denonciation/
2. Remplissez le formulaire de dénonciation
3. Cliquez sur "Soumettre"
4. Notez le code de suivi
5. Allez à http://localhost:8000/rechercher/ et testez la recherche

---

## 📊 Vérification des Configurations

### Vérifier Settings.py

```bash
python manage.py shell
```

```python
from django.conf import settings
from django.contrib.auth import get_user_model

# Vérifier le modèle User
User = get_user_model()
print(f"User model: {User}")  # Doit afficher : <class 'users.models.User'>

# Vérifier AUTH_USER_MODEL
print(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")  # Doit afficher : users.User

# Vérifier les apps installées
print(f"INSTALLED_APPS: {settings.INSTALLED_APPS}")  # Doit contenir 'users' et 'denunciations'

# Vérifier les backends
print(f"AUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")
```

### Tester l'Authentification par Email

```python
from django.contrib.auth import authenticate
from users.models import User

# Créer un utilisateur de test
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)

# Tester la connexion avec email
auth_user = authenticate(username='test@example.com', password='testpass123')
print(f"Authentifié avec email: {auth_user}")

# Tester la connexion avec username
auth_user2 = authenticate(username='testuser', password='testpass123')
print(f"Authentifié avec username: {auth_user2}")

exit()
```

---

## 🔧 Troubleshooting

### ❌ Erreur : "No module named 'users'"

**Solution** : Assurez-vous que `'users'` est dans `INSTALLED_APPS` dans `settings.py`

```python
INSTALLED_APPS = [
    ...
    'users',          # ← Doit être ici
    'denunciations',
    'core',
]
```

### ❌ Erreur : "AUTH_USER_MODEL is not set correctly"

**Solution** : Vérifiez que `settings.py` a :

```python
AUTH_USER_MODEL = 'users.User'  # ← Pas 'core.User'
```

### ❌ Erreur : "Table auth_user doesn't exist"

**Solution** : Exécutez les migrations

```bash
python manage.py migrate
```

### ❌ Templates non trouvés (404)

**Solution** : Vérifiez que `TEMPLATES['DIRS']` dans `settings.py` inclut tous les répertoires :

```python
'DIRS': [
    BASE_DIR / 'templates',
    BASE_DIR / 'users' / 'templates',
    BASE_DIR / 'denunciations' / 'templates',
    BASE_DIR / 'core' / 'templates',
]
```

### ❌ Static files non chargés

**Solution** : En développement, assurez-vous que `DEBUG = True`

```python
DEBUG = True  # ← Pour le développement
```

En production, exécutez :

```bash
python manage.py collectstatic --noinput
```

---

## 📚 Fichiers de Référence

| Fichier | Description |
|---------|-------------|
| `RESTRUCTURATION.md` | 📋 Détails techniques de la restructuration |
| `GUIDE_RESTRUCTURATION.md` | 📖 Guide complet avec étapes détaillées |
| `RESTRUCTURATION_COMPLETE.md` | ✅ Résumé complet de ce qui a été fait |
| `setup_restructuring.py` | 🔧 Script automatique de setup |
| `verify_restructuring.py` | ✅ Script de vérification (exécuté) |

---

## 🎯 Commandes Utiles

```bash
# Créer une nouvelle migration
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver

# Accéder à la console Django
python manage.py shell

# Collecte des fichiers statiques (production)
python manage.py collectstatic

# Tester l'application
python manage.py test

# Vérifier les problèmes
python manage.py check

# Afficher les migrations
python manage.py showmigrations

# Vider la base de données (⚠️ ATTENTION ⚠️)
python manage.py flush
```

---

## 📌 Points Clés à Retenir

1. **Email est l'identifiant principal** ✅
   - Inscription avec email
   - Connexion avec email
   - Email unique par utilisateur

2. **3 Rôles d'Utilisateurs** ✅
   - Travailleur : Crée/consulte ses dénonciations
   - Agent : Traite les dénonciations de sa province
   - Administrateur : Accès complet

3. **Structure des Apps** ✅
   - `users` : Authentification et gestion des utilisateurs
   - `denunciations` : Gestion des dénonciations
   - `core` : Application principale et dashboards

4. **Thème Couleurs** ✅
   - Bleu foncé : #134294
   - Gris clair : #fafafa

---

## 🎓 Tutoriels Recommandés

- [Django Authentication](https://docs.djangoproject.com/en/stable/topics/auth/)
- [Custom User Models](https://docs.djangoproject.com/en/stable/topics/auth/customizing/)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)

---

## 🚨 Mise en Garde

⚠️ **Ne supprimez PAS** :
- Les fichiers `__init__.py` (ils rendent les dossiers des packages)
- Les migrations appliquées (gardez-les dans l'historique)
- La base de données de production

✅ **Faites** :
- Sauvegardez votre base de données avant les migrations
- Testez en développement d'abord
- Lisez les erreurs Django (elles sont généralement très explicites)

---

## 📞 Support

Si vous rencontrez des problèmes :

1. ✅ Vérifiez que toutes les migrations ont été appliquées
2. ✅ Vérifiez la console Django (`python manage.py shell`)
3. ✅ Lisez les fichiers de documentation (`RESTRUCTURATION.md`, `GUIDE_RESTRUCTURATION.md`)
4. ✅ Vérifiez les logs Django

---

**Status** : ✅ Prêt pour le démarrage!

Exécutez `python setup_restructuring.py` pour commencer! 🎉
