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
]
