"""URL routes for the PySIEM operator dashboard."""

from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("events/", views.event_list, name="events"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("alerts/", views.alert_list, name="alerts"),
    path("alerts/<int:pk>/", views.alert_detail, name="alert_detail"),
    path("alerts/<int:pk>/resolve/", views.resolve_alert, name="resolve_alert"),
    path("rules/", views.rule_list, name="rules"),
    path("rules/add/", views.rule_create, name="rule_create"),
    path("rules/add/submit/", views.rule_create_submit, name="rule_create_submit"),
    path("rules/<int:pk>/edit/", views.rule_edit, name="rule_edit"),
    path("rules/<int:pk>/edit/submit/", views.rule_edit_submit, name="rule_edit_submit"),
    path("rules/<int:pk>/delete/", views.rule_delete, name="rule_delete"),
    path("rules/<int:pk>/delete/submit/", views.rule_delete_submit, name="rule_delete_submit"),
]
