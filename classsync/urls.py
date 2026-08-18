"""URL configuration for the Class Sync project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("django-admin/", admin.site.urls),  # Django built-in admin (for superuser)
    path("", include("core.urls")),
    path("admin-panel/", include("admin_panel.urls")),
    path("absence/", include("absence.urls")),
    path("attendance/", include("attendance.urls")),
    path("assignments/", include("assignments.urls")),
    path("notifications/", include("notifications.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
