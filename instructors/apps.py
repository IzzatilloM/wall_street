from django.apps import AppConfig


class InstructorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'instructors'
    verbose_name       = 'Instructorlar'

    def ready(self):
        # Foydalanuvchi <-> Instructor avtomatik sinxronlash signali
        from . import signals  # noqa: F401