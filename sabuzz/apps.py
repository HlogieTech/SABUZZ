from django.apps import AppConfig


class SabuzzConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sabuzz'

    def ready(self):
        import sabuzz.signals