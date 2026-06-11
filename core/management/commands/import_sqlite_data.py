import json
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = (
        'Import data from an old SQLite database into the default database. '
        'Useful when migrating from the local db.sqlite3 file to PostgreSQL.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--sqlite-path',
            default=str(Path(settings.BASE_DIR) / 'db.sqlite3'),
            help='Path to the old SQLite database file.',
        )
        parser.add_argument(
            '--exclude',
            nargs='*',
            default=['sessions.session', 'admin.logentry'],
            help='Model labels to exclude from the dump/load process.',
        )

    def handle(self, *args, **options):
        sqlite_path = Path(options['sqlite_path'])
        if not sqlite_path.exists():
            raise CommandError(f'Le fichier SQLite introuvable : {sqlite_path}')

        self.stdout.write(self.style.NOTICE('Configuration de la connexion SQLite ancienne base...'))

        settings.DATABASES.setdefault('old_sqlite', {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(sqlite_path),
        })
        connections.databases['old_sqlite'] = settings.DATABASES['old_sqlite']

        self.stdout.write(self.style.NOTICE('Extraction des données de l’ancienne base SQLite...'))

        apps = ['contenttypes', 'auth', 'admin', 'users', 'denunciations', 'core']
        exclude = options['exclude']

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json') as tmpfile:
            dump_path = tmpfile.name
            call_command(
                'dumpdata',
                *apps,
                database='old_sqlite',
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                exclude=exclude,
                stdout=tmpfile,
            )

        self.stdout.write(self.style.SUCCESS(f'Données exportées vers {dump_path}'))
        self.stdout.write(self.style.NOTICE('Importation des données dans PostgreSQL...'))

        try:
            call_command('loaddata', dump_path, database='default')
        except Exception as exc:
            raise CommandError(f'Erreur lors de l’import : {exc}')

        self.stdout.write(self.style.SUCCESS('Importation terminée.'))
        self.stdout.write(self.style.WARNING('Vérifiez les fichiers médias si des pièces jointes sont présentes.'))
