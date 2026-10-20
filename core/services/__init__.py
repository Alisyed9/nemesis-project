"""
PySIEM processing services (parser, rule engine, collector).

Import public helpers from this package rather than reaching into
individual modules when possible.
"""

from core.services.collector import ingest_log_source, run_collector
from core.services.parser import parse_auth_log_line
from core.services.rule_engine import (
    create_alert_for_event,
    evaluate_parsed_log,
    notify_high_severity_alert,
    prepare_alert_data,
)

__all__ = [
    "parse_auth_log_line",
    "evaluate_parsed_log",
    "prepare_alert_data",
    "create_alert_for_event",
    "notify_high_severity_alert",
    "ingest_log_source",
    "run_collector",
]
