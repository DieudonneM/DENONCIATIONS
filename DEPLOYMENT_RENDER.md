# Guide de Déploiement sur Render avec PostgreSQL

## ✅ Pré-requis Accomplis

Votre application Django est maintenant prête pour la production. Voici ce qui a été configuré :

✅ **settings.py** - Gestion automatique production/local  
✅ **requirements.txt** - Ajout de gunicorn  
✅ **Procfile** - Configuration Render  
✅ **.env.example** - Template de configuration  

---

## 🚀 Étapes pour Déployer sur Render + PostgreSQL

### **ÉTAPE 1 : Préparation Locale**

1. **Commitez vos changements sur Git** (Render va cloner votre repo)
   ```bash
   git add .
   git commit -m "Configure production deployment on Render"
   git push origin main  # ou votre branche principale
   ```

2. **Vérifiez que votre repo est sur GitHub/GitLab**
   - Render clone directement depuis GitHub/GitLab
   - Assurez-vous que votre repo est public ou connecté à Render

---

### **ÉTAPE 2 : Créer une Base de Données PostgreSQL sur Render**

1. Allez sur **[render.com](https://render.com)** et connectez-vous (créez un compte si nécessaire)

2. Cliquez sur **"New +"** → **"PostgreSQL"**

3. **Configurez la base de données :**
   - **Name** : `denunciations-db`
   - **Database** : `denunciations_app`
   - **User** : `postgres` (ou votre préférence)
   - **Region** : Sélectionnez la région la plus proche
   - **PostgreSQL Version** : 15
   - **Plan** : Free (pour le développement)

4. **Cliquez "Create Database"**

5. ⏳ **Attendez 2-3 minutes** que la base de données soit créée

6. **Copiez l'URL de connexion** (vous la verrez sur la page) - elle ressemble à :
   ```
   postgresql://user:password@host:5432/database
   ```

---

### **ÉTAPE 3 : Créer un Service Web sur Render**

1. Cliquez sur **"New +"** → **"Web Service"**

2. **Connectez votre Repository Git**
   - Choisissez "Connect a new repository"
   - Sélectionnez votre repository GitHub/GitLab
   - Cliquez "Connect"

3. **Configurez le Web Service :**

   | Paramètre | Valeur |
   |-----------|--------|
   | **Name** | `denunciations-app` |
   | **Region** | Même région que la DB |
   | **Branch** | `main` (ou votre branche) |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
   | **Start Command** | `gunicorn denunciations_app.wsgi:application` |
   | **Plan** | Free (ou Pro) |

4. **Cliquez "Create Web Service"**

---

### **ÉTAPE 4 : Configurer les Variables d'Environnement**

1. Sur la page du Web Service, allez à **"Environment"** tab

2. **Cliquez "Add Environment Variable"** et ajoutez :

   ```
   ENVIRONMENT=production
   DEBUG=False
   SECRET_KEY=<générez-une-clé-longue-et-sécurisée>
   ALLOWED_HOSTS=<your-app-name>.onrender.com
   USE_SQLITE=False
   ```

3. **Pour la base de données PostgreSQL :**
   - Allez à votre PostgreSQL database dans Render
   - Copiez l'URL de connexion complète
   - Créez une variable d'environnement :
     ```
     DB_ENGINE=django.db.backends.postgresql
     DB_NAME=denunciations_app
     DB_USER=postgres
     DB_PASSWORD=<le-mot-de-passe-de-votre-db>
     DB_HOST=<l-hôte-render>
     DB_PORT=5432
     ```

   **OU** utilisez directement l'URL complète de Render en modifiant settings.py (méthode plus simple)

4. **Cliquez "Save"**

---

### **ÉTAPE 5 : Générer une Clé Secrète Sécurisée**

En local, générez une clé Django sécurisée :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copiez la sortie et mettez-la dans `SECRET_KEY` sur Render.

---

### **ÉTAPE 6 : Déployer et Migrer**

1. **Render va automatiquement déployer** quand vous poussez du code

2. **Allez à l'onglet "Logs"** pour voir le déploiement en cours

3. **Une fois déployé**, l'app sera à : `https://<app-name>.onrender.com`

4. **Pour exécuter les migrations** :
   - Dans Render, allez à **"Console"** (à côté des Logs)
   - Exécutez :
     ```bash
     python manage.py migrate
     python manage.py createsuperuser  # Créer un compte admin
     ```

5. **Collectez les fichiers statiques** (CSS, JS)
   - Cela se fait automatiquement avec le Build Command, mais si besoin :
   ```bash
   python manage.py collectstatic --noinput
   ```

---

### **ÉTAPE 7 : Vérifier Que Tout Fonctionne**

1. Ouvrez votre app : `https://<app-name>.onrender.com`

2. **Testez les fonctionnalités principales**

3. **Accédez à l'admin Django** : `https://<app-name>.onrender.com/admin`
   - Connectez-vous avec le superuser créé

4. **Vérifiez les logs** en cas d'erreur :
   - Render → Logs
   - Recherchez les erreurs

---

## 🔒 Sécurité - À Faire ABSOLUMENT Avant Production

### Pour `settings.py` en production :

```python
# À ajouter dans settings.py si production
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

✅ **C'est déjà fait dans votre configuration !**

### Autres mesures de sécurité :

1. **N'exposez JAMAIS votre SECRET_KEY** en public
2. **Utilisez des mots de passe forts** pour PostgreSQL
3. **Activez HTTPS** (Render le fait automatiquement)
4. **Limitez ALLOWED_HOSTS** à vos domaines uniquement

---

## 🔄 Mise à Jour Continue

Pour mettre à jour votre app en production :

1. **Faites des changements localement**
2. **Testez localement** :
   ```bash
   export ENVIRONMENT=local
   python manage.py runserver
   ```
3. **Committez et poussez** :
   ```bash
   git add .
   git commit -m "Description des changements"
   git push origin main
   ```
4. **Render redéploie automatiquement**

---

## ✅ Pour Tester Localement AVANT Production

```bash
# Dans votre terminal local :

# Activez l'environnement virtuel
source venv/Scripts/activate  # Windows

# Configuration locale
export ENVIRONMENT=local
export DEBUG=True

# Testez
python manage.py runserver

# Visitez http://127.0.0.1:8000
```

---

## 🐛 Troubleshooting Render

| Problème | Solution |
|----------|----------|
| **App ne démarre pas** | Vérifiez les Logs de Render pour les erreurs |
| **Erreur 500** | Vérifiez SECRET_KEY, ALLOWED_HOSTS, la DB connection |
| **Fichiers statiques manquants** | Réexécutez `python manage.py collectstatic --noinput` |
| **Pas de base de données** | Vérifiez que PostgreSQL est créé et l'URL est correcte |
| **Migrations non exécutées** | Allez à Console et exécutez `python manage.py migrate` |

---

## 📝 Checklist Final

- [ ] Code committé et poussé sur GitHub
- [ ] PostgreSQL créé sur Render
- [ ] Web Service créé sur Render
- [ ] Variables d'environnement configurées
- [ ] Déploiement réussi (logs verts)
- [ ] Migrations exécutées
- [ ] App accessible sur HTTPS
- [ ] Admin Django fonctionne
- [ ] Fonctionnalités métier testées

---

## 🎉 C'est Fini !

Votre application est maintenant prête pour la production ! 🚀
