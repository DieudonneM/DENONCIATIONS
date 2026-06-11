"""
Django management command pour créer des comptes de démonstration.

Usage:
    python manage.py create_demo_accounts
"""

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password
from users.models import User
from denunciations.models import Province


class Command(BaseCommand):
    help = 'Crée des comptes administrateur et agents de démonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Réinitialiser les comptes existants',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)

        # Supprimer les comptes existants si --reset
        if reset:
            User.objects.filter(role__in=['administrateur', 'agent']).delete()
            self.stdout.write(self.style.WARNING('Comptes existants supprimes'))

        try:
            # ===== CRÉER UN ADMINISTRATEUR =====
            admin, created = User.objects.get_or_create(
                email='admin@mept-rdc.com',
                defaults={
                    'username': 'admin_mept',
                    'password': make_password('Admin@123456'),
                    'first_name': 'Administrateur',
                    'last_name': 'Principal',
                    'role': 'administrateur',
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS('Admin cree:')
                    + f'\n   Email: admin@mept-rdc.com'
                    + f'\n   Password: Admin@123456'
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Admin existant: admin@mept-rdc.com')
                )

            # ===== CRÉER DES PROVINCES =====
            provinces_data = [
                {'code': 'KIN', 'nom': 'Kinshasa'},
                {'code': 'KAS', 'nom': 'Kasai'},
                {'code': 'KAT', 'nom': 'Katanga'},
                {'code': 'MAC', 'nom': 'Maniema'},
                {'code': 'NOR', 'nom': 'Nord-Kivu'},
                {'code': 'SUD', 'nom': 'Sud-Kivu'},
            ]

            provinces = {}
            for prov_data in provinces_data:
                province, created = Province.objects.get_or_create(
                    code=prov_data['code'],
                    defaults={'nom': prov_data['nom']}
                )
                provinces[prov_data['code']] = province

            self.stdout.write(
                self.style.SUCCESS(f'Provinces: {len(provinces)} creees/existantes')
            )

            # ===== CRÉER DES AGENTS =====
            agents_data = [
                {
                    'email': 'agent.kinshasa@mept-rdc.com',
                    'username': 'agent_kinshasa',
                    'first_name': 'Jean',
                    'last_name': 'Mpiana',
                    'password': 'Agent@123456',
                    'provinces': ['KIN']
                },
                {
                    'email': 'agent.katanga@mept-rdc.com',
                    'username': 'agent_katanga',
                    'first_name': 'Marie',
                    'last_name': 'Tshimbo',
                    'password': 'Agent@123456',
                    'provinces': ['KAT']
                },
                {
                    'email': 'agent.nordkivu@mept-rdc.com',
                    'username': 'agent_nordkivu',
                    'first_name': 'Pierre',
                    'last_name': 'Kamanzi',
                    'password': 'Agent@123456',
                    'provinces': ['NOR', 'SUD']
                },
            ]

            for agent_data in agents_data:
                provinces_codes = agent_data.pop('provinces')
                password = agent_data.pop('password')

                agent, created = User.objects.get_or_create(
                    email=agent_data['email'],
                    defaults={
                        **agent_data,
                        'password': make_password(password),
                        'role': 'agent',
                        'is_staff': True,
                        'is_active': True,
                    }
                )

                # Assigner les provinces
                for prov_code in provinces_codes:
                    if prov_code in provinces:
                        agent.provinces.add(provinces[prov_code])

                agent.save()

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Agent cree: {agent_data["email"]}')
                        + f'\n   Password: {password}'
                        + f'\n   Provinces: {", ".join(provinces_codes)}'
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Agent existant: {agent_data["email"]}')
                    )

        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur d\'integrite: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur: {str(e)}')
            )

        # Afficher un résumé
        self.stdout.write(
            self.style.SUCCESS('\n' + '='*60)
        )
        self.stdout.write(
            self.style.SUCCESS('RESUME DES COMPTES')
        )
        self.stdout.write(
            self.style.SUCCESS('='*60)
        )

        admin_count = User.objects.filter(role='administrateur').count()
        agent_count = User.objects.filter(role='agent').count()
        worker_count = User.objects.filter(role='travailleur').count()

        self.stdout.write(f'Administrateurs: {admin_count}')
        self.stdout.write(f'Agents: {agent_count}')
        self.stdout.write(f'Travailleurs: {worker_count}')

        self.stdout.write(
            self.style.SUCCESS('='*60 + '\n')
        )
