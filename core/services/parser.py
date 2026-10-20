"""
Linux auth.log / syslog-style line parser.

Returns a dictionary whose keys match Event model fields (except `source`,
which the collector attaches from the LogSource being read).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from django.utils import timezone

from core.models import Severity

# Standard syslog prefix: "Mon  D HH:MM:SS hostname process[pid]: message"
_SYSLOG_RE = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<process>[^:]+):\s+"
    r"(?P<message>.*)$"
)

_USERNAME_PATTERNS = (
    re.compile(r"Failed password for (?:invalid user )?(?P<user>\S+) from", re.I),
    re.compile(r"Invalid user (?P<user>\S+) from", re.I),
    re.compile(r"Accepted (?:password|publickey) for (?P<user>\S+) from", re.I),
    re.compile(r"session opened for user (?P<user>\S+)", re.I),
    re.compile(r"user=(?P<user>\S+)", re.I),
    re.compile(r"USER=(?P<user>\S+)", re.I),
    re.compile(r"for user (?P<user>\S+)", re.I),
)

# IPv4, or IPv6 in common sshd "from <addr>" form.
_IP_PATTERNS = (
    re.compile(r"\bfrom (?P<ip>\d{1,3}(?:\.\d{1,3}){3})\b"),
    re.compile(r"\brhost=(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\b"),
    re.compile(r"\bfrom (?P<ip>[0-9a-fA-F:]+)\b"),
)


def parse_auth_log_line(raw_line: str) -> dict[str, Any] | None:
    """
    Parse one Linux auth.log-style line.

    Returns None if the line is empty or not syslog-shaped.
    Keys: timestamp, username, ip_address, message, raw_log, severity.
    """
    raw_log = raw_line.lstrip("\ufeff").rstrip("\r\n")
    if not raw_log.strip():
        return None

    match = _SYSLOG_RE.match(raw_log)
    if not match:
        # Unrecognized format: still keep a usable Event-shaped payload.
        now = timezone.now()
        return {
            "timestamp": now,
            "username": "",
            "ip_address": None,
            "message": raw_log,
            "raw_log": raw_log,
            "severity": Severity.LOW,
        }

    message = match.group("message").strip()
    timestamp = _parse_syslog_timestamp(
        match.group("month"),
        match.group("day"),
        match.group("time"),
    )
    return {
        "timestamp": timestamp,
        "username": _extract_username(message) or "",
        "ip_address": _extract_ip(message),
        "message": message,
        "raw_log": raw_log,
        "severity": Severity.LOW,
    }


def _parse_syslog_timestamp(month: str, day: str, time_str: str) -> datetime:
    """Build an aware datetime. Syslog lines omit the year."""
    now = timezone.now()
    try:
        naive = datetime.strptime(
            f"{now.year} {month} {int(day):02d} {time_str}",
            "%Y %b %d %H:%M:%S",
        )
    except ValueError:
        return now

    aware = timezone.make_aware(naive, timezone.get_current_timezone())
    # If the stamp sits more than a day in the future, it belongs to last year
    # (e.g. reading December logs in January).
    if aware - now > timedelta(days=1):
        aware = aware.replace(year=now.year - 1)
    return aware


def _extract_username(message: str) -> str | None:
    for pattern in _USERNAME_PATTERNS:
        found = pattern.search(message)
        if found:
            user = found.group("user").strip(" ,;")
            if user.lower() not in {"unknown", "none", "*"}:
                return user[:150]
    return None


def _extract_ip(message: str) -> str | None:
    for pattern in _IP_PATTERNS:
        found = pattern.search(message)
        if found:
            ip = found.group("ip")
            # Reject hostnames accidentally captured by the IPv6 pattern.
            if ":" in ip and not any(ch.isdigit() for ch in ip):
                continue
            return ip
    return None
