"""Smoke tests for dashboard views (queries core models only)."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Alert, DetectionRule, Event, LogSource, Severity


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

    def test_alert_list_filters_by_severity_and_shows_event_context(self):
        low_alert = Alert.objects.create(
            title="Low alert",
            description="Low priority",
            severity=Severity.LOW,
            related_event=self.event,
        )
        response = self.client.get(
            reverse("dashboard:alerts"),
            {"severity": Severity.HIGH},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alert.title)
        self.assertNotContains(response, low_alert.title)
        self.assertContains(response, self.event.message)

    def test_rule_crud_uses_form_and_messages(self):
        create_response = self.client.post(
            reverse("dashboard:rule_create_submit"),
            {
                "name": "SSH failures",
                "description": "Detect failed SSH logins",
                "pattern": r"Failed password",
                "severity": Severity.HIGH,
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(create_response.status_code, 200)
        rule = DetectionRule.objects.get(name="SSH failures")
        self.assertContains(create_response, "Detection rule &quot;SSH failures&quot; created.")

        edit_response = self.client.post(
            reverse("dashboard:rule_edit_submit", args=[rule.pk]),
            {
                "name": "SSH login failures",
                "description": "Updated description",
                "pattern": r"Failed password for",
                "severity": Severity.CRITICAL,
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(edit_response.status_code, 200)
        rule.refresh_from_db()
        self.assertEqual(rule.severity, Severity.CRITICAL)
        self.assertContains(edit_response, "Detection rule &quot;SSH login failures&quot; updated.")

        delete_response = self.client.post(
            reverse("dashboard:rule_delete_submit", args=[rule.pk]),
            follow=True,
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(DetectionRule.objects.filter(pk=rule.pk).exists())
        self.assertContains(delete_response, "Detection rule &quot;SSH login failures&quot; deleted.")
