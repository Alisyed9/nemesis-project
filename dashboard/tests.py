"""Smoke tests for dashboard views (queries core models only)."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Alert, Event, LogSource, Severity


class DashboardViewTests(TestCase):
    def setUp(self):
        self.source = LogSource.objects.create(
            name="auth",
            file_path="/tmp/auth.log",
            source_type=LogSource.SourceType.AUTH,
        )
        now = timezone.now()
        self.event = Event.objects.create(
            timestamp=now - timedelta(minutes=1),
            source=self.source,
            message="Failed password for root from 10.0.0.8",
            raw_log="raw",
            ip_address="10.0.0.8",
            username="root",
            severity=Severity.HIGH,
        )
        self.alert = Alert.objects.create(
            title="[HIGH] Detection: ssh_failed",
            description="Failed login",
            severity=Severity.HIGH,
            related_event=self.event,
            is_resolved=False,
        )

    def test_home_shows_counts_and_recent_rows(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Events")
        self.assertContains(response, "Total Alerts")
        self.assertContains(response, "Open Alerts")
        self.assertContains(response, "Failed password")
        self.assertContains(response, "[HIGH] Detection: ssh_failed")
        self.assertEqual(response.context["total_events"], 1)
        self.assertEqual(response.context["total_alerts"], 1)
        self.assertEqual(response.context["open_alerts"], 1)

    def test_resolve_alert_sets_is_resolved(self):
        url = reverse("dashboard:resolve_alert", args=[self.alert.pk])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.is_resolved)
