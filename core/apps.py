from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Application configuration for the PySIEM core domain models."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "PySIEM Core"
