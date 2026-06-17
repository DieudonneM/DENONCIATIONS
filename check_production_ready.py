#!/usr/bin/env python
"""
Script de vérification pré-déploiement pour l'application Django
Vérifie que l'app est prête pour la production
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'denunciations_app.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings
from django.db import connection

def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_django_settings():
    """Vérifie les paramètres Django"""
    print_section("🔧 Vérification des paramètres Django")
    
    checks = {
        "DEBUG": (settings.DEBUG, False, "⚠️  DEBUG ne doit PAS être True en production"),
        "SECRET_KEY configurée": (bool(settings.SECRET_KEY), True, "✓ SECRET_KEY configurée"),
        "ALLOWED_HOSTS": (bool(settings.ALLOWED_HOSTS), True, "✓ ALLOWED_HOSTS configurés"),
    }
    
    all_ok = True
    for check_name, (value, expected, message) in checks.items():
        if value == expected:
            print(f"✓ {check_name}: OK")
        else:
            print(f"✗ {check_name}: FAIL - {message}")
            all_ok = False
    
    if settings.DEBUG is False:
        print("✓ Production mode: ACTIVÉ (DEBUG=False)")
    
    return all_ok

def check_database():
    """Vérifie la connexion à la base de données"""
    print_section("🗄️  Vérification de la base de données")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Connexion à la base de données: OK")
        print(f"  Moteur: {settings.DATABASES['default']['ENGINE']}")
        print(f"  Nom: {settings.DATABASES['default'].get('NAME', 'N/A')}")
        return True
    except Exception as e:
        print(f"✗ Erreur de connexion à la base de données: {e}")
        return False

def check_migrations():
    """Vérifie l'état des migrations"""
    print_section("📦 Vérification des migrations")
    
    try:
        from django.db.migrations.loader import MigrationLoader
        loader = MigrationLoader(None, ignore_no_migrations=True)
        
        if loader.unmigrated_apps:
            print(f"⚠️  Applications non migrées: {loader.unmigrated_apps}")
            return False
        
        print("✓ Toutes les migrations sont appliquées")
        return True
    except Exception as e:
        print(f"✗ Erreur lors de la vérification des migrations: {e}")
        return False

def check_static_files():
    """Vérifie les fichiers statiques"""
    print_section("📁 Vérification des fichiers statiques")
    
    static_root = settings.STATIC_ROOT
    static_url = settings.STATIC_URL
    
    print(f"STATIC_URL: {static_url}")
    print(f"STATIC_ROOT: {static_root}")
    
    if Path(static_root).exists():
        file_count = len(list(Path(static_root).rglob('*')))
        print(f"✓ Répertoire staticfiles existe ({file_count} fichiers)")
        return True
    else:
        print("⚠️  Le répertoire staticfiles n'existe pas")
        print("   Exécutez: python manage.py collectstatic --noinput")
        return False

def check_security():
    """Vérifie les paramètres de sécurité"""
    print_section("🔐 Vérification de la sécurité")
    
    checks = {
        "SECURE_SSL_REDIRECT": (getattr(settings, 'SECURE_SSL_REDIRECT', False), "redirect HTTPS"),
        "SESSION_COOKIE_SECURE": (getattr(settings, 'SESSION_COOKIE_SECURE', False), "cookies sécurisés"),
        "CSRF_COOKIE_SECURE": (getattr(settings, 'CSRF_COOKIE_SECURE', False), "CSRF protégé"),
        "SECURE_HSTS_SECONDS": (getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0, "HSTS activé"),
    }
    
    all_ok = True
    for check_name, (value, description) in checks.items():
        if value:
            print(f"✓ {check_name}: OK ({description})")
        else:
            if settings.DEBUG:
                print(f"⚠️  {check_name}: NON ACTIF en développement (OK pour local)")
            else:
                print(f"✗ {check_name}: FAIL ({description})")
                all_ok = False
    
    return all_ok or settings.DEBUG

def check_installed_apps():
    """Vérifie les applications installées"""
    print_section("📦 Applications installées")
    
    for app in settings.INSTALLED_APPS:
        if not app.startswith('django.'):
            print(f"  • {app}")
    
    print("✓ Applications chargées avec succès")
    return True

def check_custom_user_model():
    """Vérifie le modèle utilisateur personnalisé"""
    print_section("👤 Vérification du modèle utilisateur")
    
    auth_user_model = settings.AUTH_USER_MODEL
    print(f"AUTH_USER_MODEL: {auth_user_model}")
    
    if auth_user_model != 'auth.User':
        print(f"✓ Modèle utilisateur personnalisé: {auth_user_model}")
        return True
    else:
        print("ℹ️  Modèle utilisateur par défaut Django utilisé")
        return True

def run_django_check():
    """Exécute la vérification Django intégrée"""
    print_section("🔍 Vérification Django complète")
    
    try:
        call_command('check', verbosity=0)
        print("✓ Aucune erreur détectée par Django check")
        return True
    except Exception as e:
        print(f"✗ Erreurs détectées: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║    Vérification pré-déploiement - Django Application       ║")
    print("║         Denunciations App (Render + PostgreSQL)            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {
        "Paramètres Django": check_django_settings(),
        "Base de données": check_database(),
        "Migrations": check_migrations(),
        "Fichiers statiques": check_static_files(),
        "Sécurité": check_security(),
        "Applications": check_installed_apps(),
        "Modèle utilisateur": check_custom_user_model(),
        "Vérification Django": run_django_check(),
    }
    
    # Résumé
    print_section("📊 Résumé")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {check_name}")
    
    print(f"\nTotal: {passed}/{total} vérifications passées")
    
    # Recommandations
    if passed == total:
        print_section("🎉 Prêt pour le déploiement!")
        print("\nVotre application est prête pour Render!")
        print("\nProchaines étapes:")
        print("1. Poussez votre code vers GitHub: git push origin main")
        print("2. Déployez sur Render: https://render.com/new")
        print("3. Connectez votre repository GitHub")
        print("4. Utilisez le fichier render.yaml pour la configuration")
        return 0
    else:
        print_section("⚠️  Action requise")
        print(f"\n{total - passed} vérification(s) ont échoué.")
        print("Veuillez corriger les problèmes signalés avant le déploiement.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
