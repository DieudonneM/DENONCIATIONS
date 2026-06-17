# Configuration Local vs Production

## 🏠 Mode Local (SQLite)

### Configuration
Assurez-vous que votre `.env` local contient :
```
ENVIRONMENT=local
DEBUG=True
SECRET_KEY=any-key-for-local-testing
ALLOWED_HOSTS=127.0.0.1,localhost
USE_SQLITE=True
```

### Lancer l'app
```bash
# Activez l'environnement virtuel
source venv/Scripts/activate  # Windows

# Exécutez
python manage.py runserver

# Visitez http://127.0.0.1:8000
```

### Données
- Base de données : `db.sqlite3` (fichier local)
- Les données restent sur votre ordinateur
- Médias dans `media/`

---

## 🌍 Mode Production (PostgreSQL sur Render)

### Configuration
Les variables d'environnement sur Render doivent contenir :
```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<une-clé-sécurisée-longue>
ALLOWED_HOSTS=<votre-app>.onrender.com
USE_SQLITE=False
DB_ENGINE=django.db.backends.postgresql
DB_NAME=denunciations_app
DB_USER=postgres
DB_PASSWORD=<mot-de-passe-db>
DB_HOST=<hôte-render>
DB_PORT=5432
```

### Lancer l'app
Automatique via Render (no manual action needed)

### Données
- Base de données : PostgreSQL sur Render
- Les données sont persistantes et sécurisées
- Médias dans le storage Render

---

## 📊 Différences Importantes

| Aspect | Local | Production |
|--------|-------|-----------|
| **Base de Données** | SQLite (fichier) | PostgreSQL (serveur) |
| **DEBUG** | `True` | `False` |
| **Sécurité SSL** | Non | Oui (HTTPS) |
| **Performance** | Bonne pour dev | Optimisée pour production |
| **Capacité** | Limitée | Scalable |
| **Accès Admin** | http://127.0.0.1:8000/admin | https://app.onrender.com/admin |

---

## 🔄 Workflow de Développement

```
1. Développez localement
   ↓
2. Testez localement (ENVIRONMENT=local)
   ↓
3. Committez et poussez sur Git
   ↓
4. Render déploie automatiquement
   ↓
5. Testez en production
   ↓
6. Retour à l'étape 1 si correction nécessaire
```

---

## ⚠️ Avant de Passer à Production

1. ✅ Testez localement complètement
2. ✅ Vérifiez tous les formulaires
3. ✅ Vérifiez les uploads de fichiers
4. ✅ Testez la base de données
5. ✅ Vérifiez les emails (si utilisés)
6. ✅ Collectez les fichiers statiques localement
   ```bash
   python manage.py collectstatic
   ```
7. ✅ Exécutez les migrations localement
   ```bash
   python manage.py migrate
   ```

---

## 📱 Accès Depuis Votre Téléphone

### Local (même réseau WiFi)
```
http://<your-pc-ip>:8000
```
Trouvez votre IP : `ipconfig` (Windows) ou `ifconfig` (Mac/Linux)

### Production
```
https://<votre-app>.onrender.com
```
Accessible de partout avec HTTPS

---

## 🔐 Gestion des Secrets

**JAMAIS** dans le code :
- ❌ `SECRET_KEY`
- ❌ Mots de passe
- ❌ URLs de base de données
- ❌ Tokens API

**TOUJOURS** dans `.env` :
- ✅ Fichier `.env` dans `.gitignore`
- ✅ Variables d'environnement sur Render
- ✅ Les secrets restent confidentiels

---

## 🚀 Déploiement Rapide

Après chaque changement code :

```bash
# 1. Test local
python manage.py runserver

# 2. Commit & Push
git add .
git commit -m "Description"
git push origin main

# 3. Render redéploie automatiquement
# 4. Vérifiez les logs sur Render
```

**C'est tout !** ✨
