"""
Notification utilities — re-exports from services.py for backward compatibility.

All callers should import create_notification from here, which delegates
to the push-aware version in services.py.
"""
from django.utils import timezone
from .models import Notification


def create_notification(recipient, notif_type, message, related_object_id=None):
    """
    Create and save a Notification record, then attempt push delivery.

    Delegates to services.create_notification so push is wired in exactly once.
    Uses a lazy import to avoid circular imports (services.py imports from this
    module's models, and callers in other apps import from here).
    """
    from .services import create_notification as _create
    return _create(recipient, notif_type, message, related_object_id)


def mark_all_read(user):
    """Mark all unread notifications for a user as read."""
    now = timezone.now()
    Notification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=now)


def mark_read(notification_id, user):
    """Mark a single notification as read (ownership-checked)."""
    now = timezone.now()
    Notification.objects.filter(pk=notification_id, recipient=user, read_at__isnull=True).update(read_at=now)
