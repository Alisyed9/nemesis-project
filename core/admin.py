"""Django admin registration for PySIEM core models."""

from django.contrib import admin

from core.models import Alert, DetectionRule, Event, LogSource


@admin.register(LogSource)
class LogSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "file_path", "is_active", "created_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "file_path")
    ordering = ("name",)


@admin.register(DetectionRule)
class DetectionRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "severity", "pattern", "is_active", "created_at")
    list_filter = ("severity", "is_active")
    search_fields = ("name", "description", "pattern")
    ordering = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
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
class AlertAdmin(admin.ModelAdmin):
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
