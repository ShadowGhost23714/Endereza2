# profesores/apps.py

from django.apps import AppConfig


class ProfesoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "apps.professor"
    verbose_name       = "professor"