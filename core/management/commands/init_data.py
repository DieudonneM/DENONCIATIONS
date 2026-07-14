"""
Gestion des migrations et données initiales.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Province
import os
import secrets

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialise les données de base pour l\'application'
    
    def handle(self, *args, **options):
        self.stdout.write('Création des provinces...')
        
        provinces_data = [
            ('Kinshasa', 'KIN'),
            ('Kasai', 'KAS'),
            ('Kasai-Central', 'KCT'),
            ('Kasai-Oriental', 'KOR'),
            ('Katanga', 'KAT'),
            ('Équateur', 'EQU'),
            ('Ituri', 'ITU'),
            ('Haut-Katanga', 'HKA'),
            ('Haut-Lomami', 'HLO'),
            ('Kindu', 'KIN'),
            ('Kikwit', 'KIK'),
            ('Kolwezi', 'KOL'),
            ('Likasi', 'LIK'),
            ('Maniema', 'MAN'),
            ('Mbandaka', 'MBA'),
            ('Nord-Kivu', 'NKV'),
            ('Nord-Ubangi', 'NUB'),
            ('Orientale', 'ORI'),
            ('Sud-Kivu', 'SKV'),
            ('Sud-Ubangi', 'SUB'),
            ('Tanganyika', 'TAN'),
            ('Tshopo', 'TSH'),
            ('Tshuapa', 'TSU'),
        ]
        
        for nom, code in provinces_data:
            Province.objects.get_or_create(
                nom=nom,
                defaults={'code': code}
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Province créée: {nom}'))
        
        # Créer un super utilisateur administrateur si nécessaire
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('Création du compte administrateur...')
            admin_password = os.environ.get('INIT_ADMIN_PASSWORD') or secrets.token_urlsafe(12)
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@mept-rdc.cd',
                password=admin_password,
                first_name='Admin',
                last_name='MEPT-RDC',
                role='administrateur'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Administrateur créé: {admin_user.username}')
            )
            # Afficher le mot de passe généré afin que l'administrateur puisse le récupérer
            self.stdout.write(self.style.WARNING(f'Mot de passe administrateur: {admin_password}'))
        
        self.stdout.write(self.style.SUCCESS('✓ Initialisation terminée!'))
