"""Install the repeatable sample source and detection rules."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import DetectionRule, LogSource, Severity


DEMO_RULES = (
    {
        "name": "Multiple failed SSH logins",
        "description": "Detect failed SSH password attempts for brute-force review.",
        "pattern": r"Failed password",
        "severity": Severity.HIGH,
    },
    {
        "name": "Successful login after failures",
        "description": "Flag successful SSH authentication for follow-up after failures.",
        "pattern": r"Accepted (?:password|publickey) for",
        "severity": Severity.MEDIUM,
    },
    {
        "name": "Root login detection",
        "description": "Detect direct SSH authentication as the root account.",
        "pattern": r"Accepted (?:password|publickey) for root",
        "severity": Severity.CRITICAL,
    },
    {
        "name": "Suspicious sudo usage",
        "description": "Record sudo commands for privileged activity review.",
        "pattern": r"\bCOMMAND=",
        "severity": Severity.HIGH,
    },
    {
        "name": "Invalid user login attempts",
        "description": "Detect SSH attempts against accounts that do not exist.",
        "pattern": r"Invalid user",
        "severity": Severity.HIGH,
    },
    {
        "name": "Generic error and critical patterns",
        "description": "Catch generic error, critical, fatal, or panic messages.",
        "pattern": r"\b(?:error|critical|fatal|panic)\b",
        "severity": Severity.CRITICAL,
    },
)


class Command(BaseCommand):
    help = "Create the sample auth.log source and six starter detection rules."

    def handle(self, *args, **options):
        sample_path = Path(settings.BASE_DIR) / "sample_data" / "auth.log"
        source, source_created = LogSource.objects.update_or_create(
            name="Sample auth.log",
            defaults={
                "file_path": str(sample_path),
                "source_type": LogSource.SourceType.AUTH,
                "is_active": True,
            },
        )

        created_rules = 0
        updated_rules = 0
        for rule_data in DEMO_RULES:
            _, created = DetectionRule.objects.update_or_create(
                name=rule_data["name"],
                defaults={**rule_data, "is_active": True},
            )
            if created:
                created_rules += 1
            else:
                updated_rules += 1

        source_status = "created" if source_created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: source {source_status}, "
                f"rules created={created_rules} updated={updated_rules}."
            )
        )
        self.stdout.write(f"Sample log: {sample_path}")
        self.stdout.write(
            "Next: python manage.py start_collector --once "
            f"--source-id {source.pk}"
        )