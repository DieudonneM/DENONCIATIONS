"""
Script de vérification de la structuration.
Vérifie que tous les fichiers et dossiers nécessaires sont présents.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

REQUIRED_FILES = {
    'users': [
        'users/__init__.py',
        'users/models.py',
        'users/forms.py',
        'users/views.py',
        'users/urls.py',
        'users/apps.py',
        'users/admin.py',
        'users/auth_backends.py',
        'users/signals.py',
        'users/tests.py',
        'users/migrations/__init__.py',
        'users/templates/users/auth/login.html',
        'users/templates/users/auth/register.html',
        'users/static/users/css/.gitkeep',
        'users/static/users/js/.gitkeep',
    ],
    'denunciations': [
        'denunciations/__init__.py',
        'denunciations/models.py',
        'denunciations/forms.py',
        'denunciations/views.py',
        'denunciations/urls.py',
        'denunciations/apps.py',
        'denunciations/admin.py',
        'denunciations/utils.py',
        'denunciations/signals.py',
        'denunciations/tests.py',
        'denunciations/migrations/__init__.py',
        'denunciations/static/denunciations/css/.gitkeep',
        'denunciations/static/denunciations/js/.gitkeep',
        'denunciations/templates/denunciations/.gitkeep',
    ],
    'root': [
        'denunciations_app/settings.py',
        'denunciations_app/urls.py',
        'core/models.py',
        'core/forms.py',
        'core/views.py',
        'core/urls.py',
        'RESTRUCTURATION.md',
        'GUIDE_RESTRUCTURATION.md',
        'setup_restructuring.py',
    ]
}

def check_file_exists(file_path):
    """Vérifie qu'un fichier existe."""
    full_path = BASE_DIR / file_path
    return full_path.exists()

def check_structure():
    """Vérifie la structure complète."""
    print("\n" + "="*70)
    print("VÉRIFICATION DE LA RESTRUCTURATION")
    print("="*70 + "\n")
    
    all_good = True
    
    for category, files in REQUIRED_FILES.items():
        print(f"📁 {category.upper()}")
        print("-" * 70)
        
        for file_path in files:
            exists = check_file_exists(file_path)
            status = "✅" if exists else "❌"
            print(f"  {status} {file_path}")
            
            if not exists:
                all_good = False
        
        print()
    
    # Vérification des settings.py
    print("⚙️  VÉRIFICATION DES CONFIGURATIONS")
    print("-" * 70)
    
    settings_path = BASE_DIR / 'denunciations_app' / 'settings.py'
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings_content = f.read()
        
        checks = {
            "AUTH_USER_MODEL = 'users.User'": "✅" if "AUTH_USER_MODEL = 'users.User'" in settings_content else "❌",
            "'users' dans INSTALLED_APPS": "✅" if "'users'" in settings_content else "❌",
            "'denunciations' dans INSTALLED_APPS": "✅" if "'denunciations'" in settings_content else "❌",
            "EmailBackend dans AUTHENTICATION_BACKENDS": "✅" if "EmailBackend" in settings_content else "❌",
            "LOGIN_URL = 'users:login'": "✅" if "LOGIN_URL = 'users:login'" in settings_content else "❌",
        }
        
        for check, status in checks.items():
            print(f"  {status} {check}")
            if "❌" in status:
                all_good = False
    else:
        print("  ❌ settings.py non trouvé!")
        all_good = False
    
    print()
    
    # Résumé
    print("="*70)
    if all_good:
        print("✅ TOUS LES FICHIERS SONT PRÉSENTS!")
        print("\nProchaines étapes :")
        print("  1. python manage.py makemigrations users")
        print("  2. python manage.py makemigrations denunciations")
        print("  3. python manage.py migrate")
        print("  4. python manage.py runserver")
    else:
        print("❌ CERTAINS FICHIERS MANQUENT!")
        print("\nVérifiez les fichiers marqués avec ❌")
    print("="*70 + "\n")
    
    return all_good

def create_missing_files():
    """Crée les fichiers .gitkeep manquants."""
    for category, files in REQUIRED_FILES.items():
        for file_path in files:
            if file_path.endswith('.gitkeep'):
                full_path = BASE_DIR / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                if not full_path.exists():
                    full_path.touch()
                    print(f"✅ Créé : {file_path}")

if __name__ == '__main__':
    try:
        # Créer les fichiers .gitkeep manquants
        print("Création des fichiers .gitkeep manquants...")
        create_missing_files()
        
        # Vérifier la structure
        success = check_structure()
        
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification : {e}")
        import traceback
        traceback.print_exc()
        exit(1)
