from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Application configuration for the PySIEM operator dashboard."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "PySIEM Dashboard"
