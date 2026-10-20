"""
Start PySIEM log collection from active LogSource file paths.

Usage:
    python manage.py start_collector
    python manage.py start_collector --once
    python manage.py start_collector --interval 5 --source-id 1
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.models import LogSource
from core.services.collector import run_collector


class Command(BaseCommand):
    help = (
        "Read log files from active LogSource rows, parse auth.log lines, "
        "create Event records, and create Alert records for rule matches."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Ingest current file contents and exit (no follow/tail).",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=2.0,
            help="Seconds between polls when following files (default: 2).",
        )
        parser.add_argument(
            "--source-id",
            type=int,
            default=None,
            help="Only collect from this LogSource primary key.",
        )
        parser.add_argument(
            "--path",
            dest="file_path",
            default=None,
            help="Only collect from the LogSource with this file_path.",
        )

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s %(name)s: %(message)s",
            stream=sys.stdout,
            force=True,
        )

        interval = options["interval"]
        if interval <= 0:
            raise CommandError("--interval must be greater than 0.")

        source_id = options["source_id"]
        file_path = options["file_path"]
        queryset = LogSource.objects.filter(is_active=True)
        if source_id is not None:
            queryset = queryset.filter(pk=source_id)
        if file_path:
            queryset = queryset.filter(file_path=file_path)

        sources = list(queryset)
        if not sources:
            raise CommandError(
                "No active LogSource found. Create one in /admin/ "
                "(name, file_path, source_type) and set is_active."
            )

        self.stdout.write(
            self.style.NOTICE(
                f"Starting collector for {len(sources)} source(s). "
                "High/Critical alerts print in this terminal. Ctrl+C to stop."
            )
        )
        for source in sources:
            path = Path(source.file_path)
            exists = path.is_file()
            status = "ok" if exists else "MISSING — waiting for file"
            self.stdout.write(f"  - [{source.pk}] {source.name}: {path} ({status})")

        try:
            stats_list = run_collector(
                once=options["once"],
                interval=interval,
                source_id=source_id,
                file_path=file_path,
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nCollector stopped."))
            return

        total_alerts = 0
        total_high = 0
        for stats in stats_list:
            total_alerts += stats.alerts_created
            total_high += stats.high_critical_alerts
            self.stdout.write(
                f"{stats.source_name}: lines={stats.lines_read} "
                f"events={stats.events_created} skipped={stats.skipped} "
                f"alerts={stats.alerts_created} "
                f"high_critical={stats.high_critical_alerts}"
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Collector finished. alerts={total_alerts} "
                f"high_critical={total_high}"
            )
        )
