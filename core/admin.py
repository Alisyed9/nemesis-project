"""Django admin registration for PySIEM core models."""

from django.contrib import admin, messages
from django.db import OperationalError
from django.shortcuts import redirect

from core.models import Alert, DetectionRule, Event, LogSource


class DatabaseBusyMixin:
    """Show a friendly message instead of a 500 page when SQLite is locked."""

    busy_message = (
        "Database abhi busy hai (collector chal raha hoga). "
        "Collector band karke dobara try karein."
    )

    def _busy_redirect(self, request):
        self.message_user(request, self.busy_message, level=messages.ERROR)
        opts = self.model._meta
        return redirect(f"admin:{opts.app_label}_{opts.model_name}_changelist")

    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super().delete_view(request, object_id, extra_context)
        except OperationalError:
            if request.method != "POST":
                raise
            return self._busy_redirect(request)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super().changeform_view(request, object_id, form_url, extra_context)
        except OperationalError:
            if request.method != "POST":
                raise
            return self._busy_redirect(request)

    def changelist_view(self, request, extra_context=None):
        # Covers bulk actions such as "Delete selected".
        try:
            return super().changelist_view(request, extra_context)
        except OperationalError:
            if request.method != "POST":
                raise
            return self._busy_redirect(request)


@admin.register(LogSource)
class LogSourceAdmin(DatabaseBusyMixin, admin.ModelAdmin):
    list_display = ("name", "source_type", "file_path", "is_active", "created_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "file_path")
    ordering = ("name",)


@admin.register(DetectionRule)
class DetectionRuleAdmin(DatabaseBusyMixin, admin.ModelAdmin):
    list_display = ("name", "severity", "pattern", "is_active", "created_at")
    list_filter = ("severity", "is_active")
    search_fields = ("name", "description", "pattern")
    ordering = ("name",)


@admin.register(Event)
class EventAdmin(DatabaseBusyMixin, admin.ModelAdmin):
    list_display = (
        "timestamp",
        "source",
        "severity",
        "ip_address",
        "username",
        "message",
    )
    list_filter = ("severity", "source")
    search_fields = ("message", "raw_log", "username", "ip_address")
    date_hierarchy = "timestamp"
    autocomplete_fields = ("source",)
    ordering = ("-timestamp",)


@admin.register(Alert)
class AlertAdmin(DatabaseBusyMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "severity",
        "related_event",
        "is_resolved",
        "created_at",
    )
    list_filter = ("severity", "is_resolved")
    search_fields = ("title", "description")
    autocomplete_fields = ("related_event",)
    ordering = ("-created_at",)