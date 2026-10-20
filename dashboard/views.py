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

from core.models import Alert, DetectionRule, Event, Severity

from dashboard.forms import DetectionRuleForm

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
    """Paginated alerts with status and severity filters."""
    queryset = Alert.objects.select_related(
        "related_event",
        "related_event__source",
    )
    status = request.GET.get("status", "all")
    if status == "open":
        queryset = queryset.filter(is_resolved=False)
    elif status == "resolved":
        queryset = queryset.filter(is_resolved=True)

    severity = request.GET.get("severity", "all")
    valid_severities = {choice.value for choice in Severity}
    if severity in valid_severities:
        queryset = queryset.filter(severity=severity)
    else:
        severity = "all"

    paginator = Paginator(queryset, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "dashboard/alerts.html",
        {
            "page_title": "Alerts",
            "page_obj": page,
            "status": status,
            "severity": severity,
            "severity_choices": Severity.choices,
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


@require_GET
def rule_list(request: HttpRequest) -> HttpResponse:
    """List all detection rules for operator review."""
    return render(
        request,
        "dashboard/rules.html",
        {
            "page_title": "Rules Manager",
            "rules": DetectionRule.objects.all(),
        },
    )


@require_GET
def rule_create(request: HttpRequest) -> HttpResponse:
    """Render the new detection rule form."""
    return render(
        request,
        "dashboard/rule_form.html",
        {
            "page_title": "Add Detection Rule",
            "form": DetectionRuleForm(),
            "form_heading": "Add detection rule",
        },
    )


@require_POST
def rule_create_submit(request: HttpRequest) -> HttpResponse:
    """Validate and save a new detection rule."""
    form = DetectionRuleForm(request.POST)
    if form.is_valid():
        rule = form.save()
        messages.success(request, f'Detection rule "{rule.name}" created.')
        return redirect("dashboard:rules")

    messages.error(request, "The detection rule could not be created. Check the form.")
    return render(
        request,
        "dashboard/rule_form.html",
        {
            "page_title": "Add Detection Rule",
            "form": form,
            "form_heading": "Add detection rule",
        },
        status=400,
    )


@require_GET
def rule_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """Render the edit form for an existing detection rule."""
    rule = get_object_or_404(DetectionRule, pk=pk)
    return render(
        request,
        "dashboard/rule_form.html",
        {
            "page_title": "Edit Detection Rule",
            "form": DetectionRuleForm(instance=rule),
            "form_heading": f"Edit detection rule #{rule.pk}",
            "rule": rule,
        },
    )


@require_POST
def rule_edit_submit(request: HttpRequest, pk: int) -> HttpResponse:
    """Validate and save edits to an existing detection rule."""
    rule = get_object_or_404(DetectionRule, pk=pk)
    form = DetectionRuleForm(request.POST, instance=rule)
    if form.is_valid():
        rule = form.save()
        messages.success(request, f'Detection rule "{rule.name}" updated.')
        return redirect("dashboard:rules")

    messages.error(request, "The detection rule could not be updated. Check the form.")
    return render(
        request,
        "dashboard/rule_form.html",
        {
            "page_title": "Edit Detection Rule",
            "form": form,
            "form_heading": f"Edit detection rule #{rule.pk}",
            "rule": rule,
        },
        status=400,
    )


@require_GET
def rule_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """Render a confirmation page before deleting a detection rule."""
    rule = get_object_or_404(DetectionRule, pk=pk)
    return render(
        request,
        "dashboard/rule_confirm_delete.html",
        {
            "page_title": "Delete Detection Rule",
            "rule": rule,
        },
    )


@require_POST
def rule_delete_submit(request: HttpRequest, pk: int) -> HttpResponse:
    """Delete a detection rule after confirmation."""
    rule = get_object_or_404(DetectionRule, pk=pk)
    rule_name = rule.name
    rule.delete()
    messages.success(request, f'Detection rule "{rule_name}" deleted.')
    return redirect("dashboard:rules")
