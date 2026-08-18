"""Context processor: inject unread notification count into every template."""
from .models import Notification


def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user, read_at__isnull=True
        ).count()
        recent = Notification.objects.filter(
            recipient=request.user
        ).order_by("-sent_at")[:5]
        return {"unread_count": count, "recent_notifications": recent}
    return {"unread_count": 0, "recent_notifications": []}
