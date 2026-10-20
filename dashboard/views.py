"""
Operator dashboard views.

Reads Event and Alert rows from `core.models`. Does not change models
or collection/detection services.
"""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.models import Alert, Event, Severity

RECENT_LIMIT = 15
PAGE_SIZE = 25


def _severity_counts(queryset) -> dict[str, int]:
    """Return a count for every Severity value, including zeros."""
    raw = {
        row["severity"]: row["total"]
        for row in queryset.values("severity").annotate(total=Count("id"))
    }
    return {choice.value: raw.get(choice.value, 0) for choice in Severity}


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """Summary cards plus recent events and alerts."""
    events = Event.objects.select_related("source")
    alerts = Alert.objects.select_related("related_event", "related_event__source")

    context = {
        "page_title": "Overview",
        "total_events": events.count(),
        "total_alerts": alerts.count(),
        "open_alerts": alerts.filter(is_resolved=False).count(),
        "resolved_alerts": alerts.filter(is_resolved=True).count(),
        "alert_severity_counts": _severity_counts(Alert.objects.all()),
        "recent_events": events[:RECENT_LIMIT],
        "recent_alerts": alerts[:RECENT_LIMIT],
    }
    return render(request, "dashboard/home.html", context)


@require_GET
def event_list(request: HttpRequest) -> HttpResponse:
    """Paginated table of stored events."""
    queryset = Event.objects.select_related("source")
    paginator = Paginator(queryset, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/events.html",
        {
            "page_title": "Events",
            "page_obj": page,
        },
    )


@require_GET
def event_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Single event plus alerts that reference it."""
    event = get_object_or_404(
        Event.objects.select_related("source"),
        pk=pk,
    )
    related_alerts = event.alerts.all()
    return render(
        request,
        "dashboard/event_detail.html",
        {
            "page_title": f"Event #{event.pk}",
            "event": event,
            "related_alerts": related_alerts,
        },
    )


@require_GET
def alert_list(request: HttpRequest) -> HttpResponse:
    """Paginated alerts, defaulting to open items when `?status=open`."""
    queryset = Alert.objects.select_related(
        "related_event",
        "related_event__source",
    )
    status = request.GET.get("status", "all")
    if status == "open":
        queryset = queryset.filter(is_resolved=False)
    elif status == "resolved":
        queryset = queryset.filter(is_resolved=True)

    paginator = Paginator(queryset, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/alerts.html",
        {
            "page_title": "Alerts",
            "page_obj": page,
            "status": status,
        },
    )


@require_GET
def alert_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Alert detail including the linked event."""
    alert = get_object_or_404(
        Alert.objects.select_related("related_event", "related_event__source"),
        pk=pk,
    )
    return render(
        request,
        "dashboard/alert_detail.html",
        {
            "page_title": f"Alert #{alert.pk}",
            "alert": alert,
        },
    )


@require_POST
def resolve_alert(request: HttpRequest, pk: int) -> HttpResponse:
    """Mark an alert resolved (`is_resolved=True`) without deleting it."""
    alert = get_object_or_404(Alert, pk=pk)
    if alert.is_resolved:
        messages.info(request, f"Alert #{alert.pk} is already resolved.")
    else:
        alert.is_resolved = True
        alert.save(update_fields=["is_resolved"])
        messages.success(request, f"Alert #{alert.pk} marked as resolved.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url:
        return redirect(next_url)
    return redirect("dashboard:alert_detail", pk=alert.pk)
