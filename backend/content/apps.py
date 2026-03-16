from django.apps import AppConfig


class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'

    def ready(self):
        import projectapp.tasks  # noqa: F401 — Huey periodic task discovery
