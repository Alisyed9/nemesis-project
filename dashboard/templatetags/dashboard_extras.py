"""Template helpers for severity coloring on the dashboard."""

from django import template

register = template.Library()

_BADGE_CLASSES = {
    "critical": "severity-critical",
    "high": "severity-high",
    "medium": "severity-medium",
    "low": "severity-low",
}

_ROW_CLASSES = {
    "critical": "row-critical",
    "high": "row-high",
    "medium": "row-medium",
    "low": "row-low",
}


@register.filter
def severity_badge(severity: str) -> str:
    """CSS class for a severity pill."""
    return _BADGE_CLASSES.get(severity, "severity-low")


@register.filter
def severity_row(severity: str) -> str:
    """CSS class for a table row tinted by severity."""
    return _ROW_CLASSES.get(severity, "")
