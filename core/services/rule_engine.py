"""
Detection against active DetectionRule rows, plus a simple correlation rule.

When a match is found, `create_alert_for_event` persists an Alert linked
to the related Event. High/Critical hits also print a terminal notice.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.utils import timezone

from core.models import Alert, DetectionRule, Event, Severity

logger = logging.getLogger(__name__)

# Correlation: N failed logins from the same IP inside this window.
FAILED_LOGIN_WINDOW = timedelta(minutes=2)
FAILED_LOGIN_THRESHOLD = 5
FAILED_LOGIN_MESSAGE_RE = re.compile(
    r"Failed password|authentication failure|Invalid user|Failed publickey",
    re.IGNORECASE,
)

_SEVERITY_RANK = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

HIGH_SEVERITIES = frozenset({Severity.HIGH, Severity.CRITICAL})


@dataclass(frozen=True)
class RuleMatch:
    """One signature or correlation hit for a parsed log line."""

    rule_name: str
    severity: str
    pattern: str
    rule_id: int | None = None


def load_active_rules() -> list[DetectionRule]:
    """Fetch enabled DetectionRule rows for matching."""
    return list(DetectionRule.objects.filter(is_active=True).order_by("name"))


def evaluate_parsed_log(
    parsed: dict[str, Any],
    *,
    include_unsaved_failure: bool = True,
) -> list[RuleMatch]:
    """
    Match `parsed["message"]` against active rule regexes and apply
    failed-login correlation for the extracted IP.
    """
    message = parsed.get("message") or ""
    matches = match_rules(message)

    correlation = detect_failed_login_burst(
        ip_address=parsed.get("ip_address"),
        timestamp=parsed.get("timestamp") or timezone.now(),
        message=message,
        include_current=include_unsaved_failure,
    )
    if correlation:
        matches.append(correlation)
    return matches


def match_rules(message: str) -> list[RuleMatch]:
    """Run stored DetectionRule.pattern values as regular expressions."""
    hits: list[RuleMatch] = []
    for rule in load_active_rules():
        compiled = _compile_pattern(rule.pattern)
        if compiled is None:
            continue
        if compiled.search(message):
            hits.append(
                RuleMatch(
                    rule_id=rule.pk,
                    rule_name=rule.name,
                    severity=rule.severity,
                    pattern=rule.pattern,
                )
            )
    return hits


def detect_failed_login_burst(
    ip_address: str | None,
    timestamp,
    message: str,
    *,
    include_current: bool = True,
) -> RuleMatch | None:
    """
    Flag brute-force style activity: several failed logins from one IP
    within FAILED_LOGIN_WINDOW.
    """
    if not ip_address or not FAILED_LOGIN_MESSAGE_RE.search(message):
        return None

    window_start = timestamp - FAILED_LOGIN_WINDOW
    prior = Event.objects.filter(
        ip_address=ip_address,
        timestamp__gte=window_start,
        timestamp__lte=timestamp,
        message__iregex=FAILED_LOGIN_MESSAGE_RE.pattern,
    ).count()

    # Count this line even though the Event may not be saved yet.
    total = prior + (1 if include_current else 0)
    if total < FAILED_LOGIN_THRESHOLD:
        return None

    return RuleMatch(
        rule_id=None,
        rule_name="correlated_failed_logins",
        severity=Severity.HIGH,
        pattern=(
            f">={FAILED_LOGIN_THRESHOLD} failed logins from {ip_address} "
            f"within {int(FAILED_LOGIN_WINDOW.total_seconds())}s"
        ),
    )


def highest_severity(matches: list[RuleMatch], default: str = Severity.LOW) -> str:
    """Return the most severe label among matches."""
    if not matches:
        return default
    return max(matches, key=lambda item: _SEVERITY_RANK.get(item.severity, 0)).severity


def prepare_alert_data(event: Event, matches: list[RuleMatch]) -> dict[str, Any]:
    """Build Alert field values from an Event and its rule matches."""
    severity = highest_severity(matches, default=event.severity)
    names = ", ".join(match.rule_name for match in matches)
    title = _marked_title(f"Detection: {names}", severity)
    description = (
        f"Source: {event.source.name}\n"
        f"User: {event.username or '-'}\n"
        f"IP: {event.ip_address or '-'}\n"
        f"Message: {event.message}\n"
        f"Matched: {names}"
    )
    return {
        "title": title,
        "description": description,
        "severity": severity,
        "related_event": event,
        "related_event_id": event.pk,
        "matched_rules": [
            {
                "rule_id": match.rule_id,
                "name": match.rule_name,
                "severity": match.severity,
                "pattern": match.pattern,
            }
            for match in matches
        ],
    }


def create_alert_for_event(event: Event, matches: list[RuleMatch]) -> Alert | None:
    """
    Persist one Alert linked to `event` when the rule engine found matches.

    Does not create an Alert when `matches` is empty.
    """
    if not matches:
        return None

    payload = prepare_alert_data(event, matches)
    alert = Alert.objects.create(
        title=payload["title"],
        description=payload["description"],
        severity=payload["severity"],
        related_event=event,
        is_resolved=False,
    )
    logger.info(
        "Created alert id=%s severity=%s event_id=%s title=%s",
        alert.pk,
        alert.severity,
        event.pk,
        alert.title,
    )
    notify_high_severity_alert(alert)
    return alert


def notify_high_severity_alert(alert: Alert) -> None:
    """
    Terminal placeholder for High/Critical notifications.

    Email / webhook delivery belongs in a later milestone.
    """
    if alert.severity not in HIGH_SEVERITIES:
        return

    label = alert.get_severity_display().upper()
    event = alert.related_event
    banner = "=" * 72
    message = (
        f"\n{banner}\n"
        f"!!! {label} ALERT !!!\n"
        f"Alert ID : {alert.pk}\n"
        f"Title    : {alert.title}\n"
        f"Event ID : {event.pk}\n"
        f"Source   : {event.source.name}\n"
        f"User     : {event.username or '-'}\n"
        f"IP       : {event.ip_address or '-'}\n"
        f"Message  : {event.message}\n"
        f"{banner}\n"
    )
    print(message, flush=True)
    logger.warning("%s alert created: id=%s title=%s", label, alert.pk, alert.title)


def _marked_title(title: str, severity: str) -> str:
    """Prefix High/Critical titles so they stand out in admin and the dashboard."""
    if severity == Severity.CRITICAL:
        prefix = "[CRITICAL] "
    elif severity == Severity.HIGH:
        prefix = "[HIGH] "
    else:
        prefix = ""
    return f"{prefix}{title}"[:200]


def _compile_pattern(pattern: str) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        logger.warning("Skipping invalid DetectionRule pattern %r: %s", pattern, exc)
        return None
