from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Gestion des Dénonciations'
    
    def ready(self):
        """Enregistrer les signaux lors du chargement de l'application."""
        import core.signals  # noqa
