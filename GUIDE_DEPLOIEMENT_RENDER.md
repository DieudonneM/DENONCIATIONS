# Guide de Déploiement sur Render + PostgreSQL

## 📋 Table des matières
1. [Prérequis](#prérequis)
2. [Configuration locale](#configuration-locale)
3. [Préparation pour production](#préparation-pour-production)
4. [Déploiement sur Render](#déploiement-sur-render)
5. [Vérification et maintenance](#vérification-et-maintenance)

---

## 🔧 Prérequis

### Avant de commencer, assurez-vous d'avoir :
- [Git](https://git-scm.com/) installé
- Un compte [Render](https://render.com) (gratuit)
- [Python 3.10+](https://www.python.org/)
- [PostgreSQL](https://www.postgresql.org/) (optionnel pour le test local)

---

## 📍 Configuration locale

### 1. Vérifier que le serveur de développement fonctionne

```bash
# Assurez-vous que vous êtes dans le dossier du projet
cd c:\Users\dmuhe\Documents\DJANGO\denunciations_app

# Activez votre environnement virtuel
.\venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac

# Installez les dépendances
pip install -r requirements.txt

# Lancez le serveur local
python manage.py runserver
```

✅ Vous devriez voir : `Starting development server at http://127.0.0.1:8000/`

### 2. Tester avec SQLite (développement)

Le `.env` local doit contenir :
```
DEBUG=True
USE_SQLITE=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

### 3. Tester avec PostgreSQL (optionnel, pour valider avant la production)

```bash
# Créez une base de données PostgreSQL locale
createdb denunciations_app

# Mettez à jour le .env
DEBUG=True
USE_SQLITE=False
DB_NAME=denunciations_app
DB_USER=postgres
DB_PASSWORD=<votre-mot-de-passe>
DB_HOST=127.0.0.1
DB_PORT=5432

# Exécutez les migrations
python manage.py migrate

# Lancez le serveur
python manage.py runserver
```

---

## 🚀 Préparation pour production

### 1. Générer une clé secrète forte

```bash
# Générez une nouvelle SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Copiez la clé générée et gardez-la en sécurité.

### 2. Nettoyer l'application

```bash
# Collectez les fichiers statiques
python manage.py collectstatic --noinput

# Vérifiez qu'il n'y a pas d'erreurs
python manage.py check
```

### 3. Vérifier les paramètres de production dans settings.py

Les configurations suivantes sont déjà en place :
- ✅ HTTPS redirection
- ✅ Sécurité des cookies (SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE)
- ✅ HSTS (HTTP Strict Transport Security)
- ✅ Compression des fichiers statiques avec WhiteNoise

### 4. Initialiser Git (si ce n'est pas déjà fait)

```bash
# Initialisez le repository Git
git init

# Ajoutez tous les fichiers
git add .

# Créez un commit initial
git commit -m "Initial commit: Django app ready for Render"

# Ajoutez le remote (vous verrez l'URL sur Render)
git remote add origin https://github.com/votre-username/votre-repo.git

# Poussez le code
git push -u origin main
```

---

## 🌐 Déploiement sur Render

### Étape 1 : Créer un compte Render

1. Allez sur [render.com](https://render.com)
2. Inscrivez-vous gratuitement
3. Connectez votre compte GitHub

### Étape 2 : Connecter votre dépôt GitHub

1. Sur le tableau de bord Render, cliquez sur **"New +"**
2. Sélectionnez **"Blueprint"**
3. Collez l'URL de votre dépôt GitHub
4. Donnez un nom à votre service (ex: `denunciations-app`)
5. Cliquez sur **"Create Blueprint"**

### Étape 3 : Configuration automatique (render.yaml)

Render lira automatiquement le fichier `render.yaml` et créera :
- ✅ Un service web Django
- ✅ Une base de données PostgreSQL

### Étape 4 : Définir les variables d'environnement

Si le `render.yaml` ne suffit pas, allez à **Settings → Environment Variables** et ajoutez :

| Clé | Valeur |
|-----|--------|
| `DEBUG` | `False` |
| `USE_SQLITE` | `False` |
| `SECRET_KEY` | *(la clé générée plus tôt)* |
| `ALLOWED_HOSTS` | `denunciations-app.onrender.com` |
| `SECURE_SSL_REDIRECT` | `True` |
| `SESSION_COOKIE_SECURE` | `True` |
| `CSRF_COOKIE_SECURE` | `True` |

Les variables `DB_*` sont générées automatiquement par Render.

### Étape 5 : Lancer le déploiement

1. Cliquez sur **"Deploy"**
2. Attendez que les logs disent **"Deployed successfully"**
3. Votre app sera disponible à `https://denunciations-app.onrender.com`

---

## 📊 Vérification et maintenance

### Vérifier que le déploiement fonctionne

```bash
# Allez sur votre app Render
https://denunciations-app.onrender.com

# Vérifiez l'admin
https://denunciations-app.onrender.com/admin

# Consultez les logs
# Depuis le tableau de bord Render → Logs
```

### Créer un superutilisateur en production

```bash
# Via la console Render
render bash denunciations-app

# Une fois dans la console
python manage.py createsuperuser
```

### Migrer les données existantes

```bash
# Depuis votre machine locale
python manage.py dumpdata > backup.json

# Puis sur Render (via sa console)
python manage.py loaddata backup.json
```

### Redéployer après des modifications

```bash
# Depuis votre machine locale
git add .
git commit -m "Mes modifications"
git push origin main

# Render redéploiera automatiquement
```

### Consulter les logs en production

1. Allez sur le tableau de bord Render
2. Cliquez sur votre service
3. Onglet **"Logs"** : voir les logs en temps réel

---

## ⚠️ Points importants

### Sécurité
- **JAMAIS** partager la `SECRET_KEY` dans le code
- Utilisez les variables d'environnement de Render
- Activez HTTPS (Render le fait automatiquement)

### Base de données
- Render crée une base PostgreSQL gratuite
- Les données sont persistantes
- Faites des sauvegardes régulières

### Performance
- La formule gratuite de Render peut être lente
- Pour la production, passez à un plan payant

### Dépannage courant

| Erreur | Solution |
|--------|----------|
| `ModuleNotFoundError` | Vérifiez que `requirements.txt` est à jour |
| `DatabaseError` | Vérifiez les variables `DB_*` |
| `DisallowedHost` | Mettez à jour `ALLOWED_HOSTS` avec votre domaine Render |
| `Static files 404` | Exécutez `collectstatic` lors du déploiement |

---

## 📚 Ressources utiles

- [Documentation Render Django](https://docs.render.com/deploy-django)
- [Documentation Django Deployment](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [PostgreSQL sur Render](https://docs.render.com/databases)

---

**Bonne chance pour votre déploiement ! 🚀**
