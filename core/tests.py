"""Tests for parsing, rule matching, and end-to-end collection."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from core.models import Alert, DetectionRule, LogSource, Severity
from core.management.commands.seed_demo_data import DEMO_RULES
from core.services.collector import ingest_log_source


class CollectorFlowTests(TestCase):
	def test_demo_rules_include_all_required_signatures(self):
		self.assertEqual(len(DEMO_RULES), 6)
		rule_names = {rule["name"] for rule in DEMO_RULES}
		self.assertSetEqual(
			rule_names,
			{
				"Multiple failed SSH logins",
				"Successful login after failures",
				"Root login detection",
				"Suspicious sudo usage",
				"Invalid user login attempts",
				"Generic error and critical patterns",
			},
		)

	def test_auth_log_creates_events_and_alerts(self):
		DetectionRule.objects.create(
			name="Failed SSH",
			pattern=r"Failed password",
			severity=Severity.HIGH,
		)

		with TemporaryDirectory() as directory:
			log_path = Path(directory) / "auth.log"
			log_path.write_text(
				"Oct 20 09:00:01 nemesis sshd[2101]: "
				"Failed password for root from 203.0.113.50 port 42100 ssh2\n"
				"Oct 20 09:00:12 nemesis sshd[2102]: "
				"Failed password for root from 203.0.113.50 port 42101 ssh2\n",
				encoding="utf-8",
			)
			source = LogSource.objects.create(
				name="Test auth.log",
				file_path=str(log_path),
				source_type=LogSource.SourceType.AUTH,
			)

			stats, new_offset = ingest_log_source(source)

		self.assertGreater(new_offset, 0)
		self.assertEqual(stats.lines_read, 2)
		self.assertEqual(stats.events_created, 2)
		self.assertEqual(stats.alerts_created, 2)
		self.assertEqual(Alert.objects.count(), 2)
		self.assertEqual(Alert.objects.first().severity, Severity.HIGH)
