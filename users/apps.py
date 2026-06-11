from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Gestion des utilisateurs'
    
    def ready(self):
        """Importer les signaux au démarrage."""
        import users.signals  # noqa
