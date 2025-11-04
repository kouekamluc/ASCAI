from django.apps import AppConfig


class ForumsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.forums"
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.forums.signals