"""
Root URL configuration for PySIEM.

Admin remains at /admin/. Operator dashboard is the site root.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
]

handler404 = "pysiem.views.page_not_found"
handler500 = "pysiem.views.server_error"
