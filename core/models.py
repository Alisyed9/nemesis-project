"""
PySIEM core domain models.

This module is the shared data layer for later milestones (log collector,
parser, rule engine, and dashboard). Import models from `core.models`.
"""

from django.db import models


class Severity(models.TextChoices):
    """Shared severity scale used by rules, events, and alerts."""

    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class LogSource(models.Model):
    """
    A monitored origin of security logs (file path, syslog feed, etc.).

    Later milestones will poll `file_path` when `is_active` is True.
    """

    class SourceType(models.TextChoices):
        AUTH = "auth", "Auth / syslog"
        APACHE = "apache", "Apache / web"
        WINDOWS = "windows", "Windows event"
        APPLICATION = "application", "Application"
        CUSTOM = "custom", "Custom"

    name = models.CharField(max_length=150, unique=True)
    file_path = models.CharField(
        max_length=500,
        help_text="Absolute path to the log file this source reads from.",
    )
    source_type = models.CharField(
        max_length=32,
        choices=SourceType.choices,
        default=SourceType.CUSTOM,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Log source"
        verbose_name_plural = "Log sources"

    def __str__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"{self.name} ({self.get_source_type_display()}, {status})"


class DetectionRule(models.Model):
    """
    A signature used to flag interesting log lines.

    `pattern` is intended for the future rule engine (regex or simple
    substring matching). Do not evaluate patterns in Milestone 1.
    """

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    pattern = models.CharField(
        max_length=500,
        help_text="Match pattern (regex or keyword) applied to parsed log lines.",
    )
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Detection rule"
        verbose_name_plural = "Detection rules"

    def __str__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"{self.name} [{self.get_severity_display()}] ({status})"


class Event(models.Model):
    """
    A normalized security event produced from a raw log line.

    The collector/parser (future milestones) should populate `raw_log`
    plus extracted fields such as IP address and username.
    """

    timestamp = models.DateTimeField(
        help_text="Time the original log entry occurred, not ingest time.",
    )
    source = models.ForeignKey(
        LogSource,
        on_delete=models.CASCADE,
        related_name="events",
    )
    message = models.TextField()
    raw_log = models.TextField(
        help_text="Original unmodified log line for forensics.",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    username = models.CharField(max_length=150, blank=True)
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.LOW,
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["severity"]),
        ]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self) -> str:
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} | {self.get_severity_display()} | {self.source.name}"


class Alert(models.Model):
    """
    An actionable notification created when a detection rule matches an event.

    `related_event` points at the Event that triggered this alert.
    Resolution is a manual operator action for now (`is_resolved`).
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.MEDIUM,
    )
    related_event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_resolved", "-created_at"]),
            models.Index(fields=["severity"]),
        ]
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    def __str__(self) -> str:
        state = "resolved" if self.is_resolved else "open"
        return f"{self.title} [{self.get_severity_display()}] ({state})"
