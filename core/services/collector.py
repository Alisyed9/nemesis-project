from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from django.db import IntegrityError, OperationalError, transaction

from core.models import Alert, Event, LogSource
from core.services.parser import parse_auth_log_line
from core.services.rule_engine import (
    HIGH_SEVERITIES,
    create_alert_for_event,
    evaluate_parsed_log,
    highest_severity,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


def run_with_retry(fn: Callable[[], T], retries: int = 5, delay: float = 0.5) -> T:
    """
    Run `fn` inside one atomic transaction.

    If SQLite reports "database is locked", wait and retry. Because the whole
    call is atomic, a failed attempt rolls back completely (no partial data).
    """
    for attempt in range(1, retries + 1):
        try:
            with transaction.atomic():
                return fn()
        except OperationalError as exc:
            if "locked" in str(exc).lower() and attempt < retries:
                logger.warning("Database locked, retry %s/%s", attempt, retries)
                time.sleep(delay * attempt)
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


@dataclass
class IngestStats:
    """Result of processing one source file (or a chunk of new lines)."""

    source_id: int
    source_name: str
    lines_read: int = 0
    events_created: int = 0
    skipped: int = 0
    alerts_created: int = 0
    high_critical_alerts: int = 0
    created_alerts: list[Alert] = field(default_factory=list)


def ingest_log_source(
    source: LogSource,
    *,
    offset: int = 0,
) -> tuple[IngestStats, int]:
    """
    Read `source.file_path` from `offset` to EOF.

    Returns (stats, new_offset). The whole chunk is saved atomically, so if
    this raises, nothing was saved and the caller keeps the old offset.
    """
    stats = IngestStats(source_id=source.pk, source_name=source.name)
    path = Path(source.file_path)
    if not path.is_file():
        logger.warning("Log source %s path does not exist: %s", source.name, path)
        return stats, offset

    size = path.stat().st_size
    if size < offset:
        # File was rotated/truncated: start from the beginning.
        offset = 0

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(offset)
        chunk = handle.read()
        new_offset = handle.tell()

    if not chunk:
        return stats, new_offset

    lines = chunk.splitlines()

    def _attempt() -> IngestStats:
        # Fresh stats on every attempt so retries never double-count.
        attempt_stats = IngestStats(source_id=source.pk, source_name=source.name)
        attempt_stats.lines_read = len(lines)
        _process_lines(source, lines, attempt_stats)
        return attempt_stats

    stats = run_with_retry(_attempt)
    return stats, new_offset


def run_collector(
    *,
    once: bool = False,
    interval: float = 2.0,
    source_id: int | None = None,
    file_path: str | None = None,
    stop_after: int | None = None,
) -> list[IngestStats]:
    """
    Monitor active LogSource files.

    When `once` is True, ingest current file contents and return.
    Otherwise poll for new bytes until interrupted (or `stop_after` loops,
    used by tests).
    """
    sources = _select_sources(source_id=source_id, file_path=file_path)
    if not sources:
        logger.warning("No active LogSource rows matched; nothing to collect.")
        return []

    offsets: dict[int, int] = {source.pk: 0 for source in sources}
    last_stats: dict[int, IngestStats] = {}
    loops = 0

    while True:
        # Refresh source list each cycle so admin changes/deletes take effect.
        sources = _select_sources(source_id=source_id, file_path=file_path)
        for source in sources:
            offsets.setdefault(source.pk, 0)
            try:
                stats, offsets[source.pk] = ingest_log_source(
                    source,
                    offset=offsets[source.pk],
                )
            except (OperationalError, IntegrityError):
                # Offset was not advanced, so this chunk is retried next cycle.
                logger.exception(
                    "Database error while ingesting source %s; will retry.",
                    source.name,
                )
                if once:
                    raise
                continue

            last_stats[source.pk] = stats
            if stats.events_created or stats.alerts_created:
                logger.info(
                    "source=%s events=%s alerts=%s high_critical=%s",
                    source.name,
                    stats.events_created,
                    stats.alerts_created,
                    stats.high_critical_alerts,
                )

        loops += 1
        if once or (stop_after is not None and loops >= stop_after):
            break
        time.sleep(max(interval, 0.2))

    return list(last_stats.values())


def _select_sources(
    *,
    source_id: int | None,
    file_path: str | None,
) -> list[LogSource]:
    queryset = LogSource.objects.filter(is_active=True)
    if source_id is not None:
        queryset = queryset.filter(pk=source_id)
    if file_path:
        queryset = queryset.filter(file_path=file_path)
    return list(queryset)


def _process_lines(
    source: LogSource,
    lines: Iterable[str],
    stats: IngestStats,
) -> None:
    for line in lines:
        parsed = parse_auth_log_line(line)
        if parsed is None:
            stats.skipped += 1
            continue

        matches = evaluate_parsed_log(parsed)
        severity = highest_severity(matches, default=parsed["severity"])

        event = Event.objects.create(
            timestamp=parsed["timestamp"],
            source=source,
            message=parsed["message"],
            raw_log=parsed["raw_log"],
            ip_address=parsed["ip_address"],
            username=parsed["username"],
            severity=severity,
        )
        stats.events_created += 1

        if not matches:
            continue

        alert = create_alert_for_event(event, matches)
        if alert is None:
            continue
        stats.created_alerts.append(alert)
        stats.alerts_created += 1
        if alert.severity in HIGH_SEVERITIES:
            stats.high_critical_alerts += 1