# ✅ Production Readiness Checklist

Avant de déployer sur Render, assurez-vous de cocher tous les éléments suivants :

## 🔐 Sécurité

- [ ] **SECRET_KEY** : Générez une nouvelle clé secrète
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```

- [ ] **DEBUG = False** : Vérifiez que `DEBUG=False` en production

- [ ] **ALLOWED_HOSTS** : Configuré avec votre domaine Render
  - [ ] Format : `denunciations-app.onrender.com`

- [ ] **HTTPS** : Activé automatiquement par Render

- [ ] **Cookies sécurisés** :
  - [ ] `SESSION_COOKIE_SECURE = True`
  - [ ] `CSRF_COOKIE_SECURE = True`

- [ ] **HSTS** : Activé dans settings.py

- [ ] **.env.example** : Crée pour documenter les variables

---

## 📦 Dépendances

- [ ] **requirements.txt** : Mis à jour avec toutes les dépendances
  - [ ] `Django==4.2.11`
  - [ ] `psycopg2-binary==2.9.9` (PostgreSQL)
  - [ ] `gunicorn==21.2.0` (serveur web)
  - [ ] `whitenoise==6.6.0` (fichiers statiques)
  - [ ] `python-decouple==3.8` (variables d'environnement)

- [ ] **Procfile** : Créé avec les commandes de déploiement
  ```
  release: python manage.py migrate
  web: gunicorn denunciations_app.wsgi
  ```

- [ ] **render.yaml** : Configuré avec la base de données PostgreSQL

---

## 🗄️ Base de données

- [ ] **PostgreSQL** : Sera créé automatiquement par Render

- [ ] **Migrations** : Toutes les migrations sont appliquées
  ```bash
  python manage.py migrate --check
  ```

- [ ] **Fixtures/Données initiales** : Chargées si nécessaire

---

## 📁 Fichiers statiques

- [ ] **STATIC_URL** : Configuré correctement
  - [ ] `STATIC_URL = '/static/'`

- [ ] **STATIC_ROOT** : Points vers `BASE_DIR / 'staticfiles'`

- [ ] **WhiteNoise** : Activé dans MIDDLEWARE

- [ ] **collectstatic** : Testé localement
  ```bash
  python manage.py collectstatic --noinput
  ```

- [ ] **Média** : Configuration si nécessaire
  - [ ] `MEDIA_URL = '/media/'`
  - [ ] `MEDIA_ROOT` = `BASE_DIR / 'media'`

---

## 🧪 Tests

- [ ] **Tests locaux** : Passez en développement
  ```bash
  python manage.py test
  ```

- [ ] **Check Django** : Pas d'erreurs
  ```bash
  python manage.py check
  ```

- [ ] **Serveur local** : Fonctionne avec PostgreSQL
  ```bash
  python manage.py runserver
  ```

---

## 📝 Contrôle de code

- [ ] **Git** : Repository initialisé et connecté à GitHub
  ```bash
  git status
  git remote -v
  ```

- [ ] **Fichiers sensibles** : Pas d'exposition de secrets
  - [ ] `.env` n'est PAS dans Git (utilisez `.env.example`)
  - [ ] `db.sqlite3` n'est PAS dans Git
  - [ ] `staticfiles/` n'est PAS dans Git

- [ ] **.gitignore** : Correctement configuré
  ```
  .env
  db.sqlite3
  venv/
  __pycache__/
  *.pyc
  staticfiles/
  media/
  ```

---

## 🚀 Prêt pour le déploiement

- [ ] Tous les éléments ci-dessus sont cochés ✅

- [ ] Avez-vous un compte Render ? [render.com](https://render.com)

- [ ] Votre repo GitHub est public ou accessible par Render

---

## 📋 Commandes de test pré-déploiement

```bash
# 1. Vérifiez les dépendances
pip install -r requirements.txt

# 2. Vérifiez la configuration Django
python manage.py check

# 3. Testez la collecte des fichiers statiques
python manage.py collectstatic --noinput

# 4. Testez les migrations
python manage.py migrate --plan  # Voir ce qui sera appliqué
python manage.py migrate         # Appliquer les migrations

# 5. Lancez le serveur local
python manage.py runserver

# 6. Poussez le code vers GitHub
git add .
git commit -m "Production ready"
git push origin main
```

---

## 🎯 Prochaines étapes

1. ✅ **Cochez tous les éléments** de cette checklist
2. 📤 **Poussez vers GitHub** : `git push origin main`
3. 🌐 **Déployez sur Render** : Suivez le [guide de déploiement](./GUIDE_DEPLOIEMENT_RENDER.md)
4. 🔍 **Testez l'app en production** : Visitez votre URL Render
5. 📊 **Consultez les logs** : Depuis le tableau de bord Render

---

**Date de préparation** : 2026-06-17
**Application** : Django Denunciations App
**Environnement cible** : Render + PostgreSQL
