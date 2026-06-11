#!/usr/bin/env python
"""
Script pour exécuter les migrations et préparer la restructuration.
À exécuter après les modifications de structure.
"""

import os
import sys
import django
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'denunciations_app.settings')

# Ajouter le répertoire du projet au chemin
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
django.setup()

from django.core.management import call_command
from django.core.management import execute_from_command_line

def run_migrations():
    """Exécuter toutes les migrations."""
    print("\n" + "="*70)
    print("RESTRUCTURATION - Plateforme de Dénonciation MEPT-RDC")
    print("="*70 + "\n")
    
    print("✓ Création des migrations pour 'users'...")
    call_command('makemigrations', 'users', verbosity=1)
    
    print("\n✓ Création des migrations pour 'denunciations'...")
    call_command('makemigrations', 'denunciations', verbosity=1)
    
    print("\n✓ Application des migrations...")
    call_command('migrate', verbosity=1)
    
    print("\n" + "="*70)
    print("✅ RESTRUCTURATION COMPLÉTÉE AVEC SUCCÈS!")
    print("="*70)
    print("\nProchaines étapes :")
    print("1. Vérifiez que les migrations sont appliquées")
    print("2. Déplacez les templates existants si nécessaire")
    print("3. Testez l'authentification par email")
    print("4. Vérifiez les couleurs du thème")
    print("\nCommandes utiles :")
    print("  python manage.py createsuperuser")
    print("  python manage.py runserver")
    print("\n")

if __name__ == '__main__':
    try:
        run_migrations()
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution : {e}")
        sys.exit(1)
