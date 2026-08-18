"""Notifications app views: notification center, mark read, risk flags."""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from core.decorators import role_required
from .models import Notification, RiskFlag
from .utils import mark_all_read, mark_read


@login_required
def notification_center(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-sent_at")[:50]
    return render(request, "notifications/center.html", {"notifications": notifications})


@login_required
def mark_notification_read(request, pk):
    mark_read(pk, request.user)
    referer = request.META.get("HTTP_REFERER")
    return redirect(referer if referer else reverse("notifications:center"))


@login_required
def mark_all_notifications_read(request):
    mark_all_read(request.user)
    return redirect("notifications:center")


@role_required("faculty", "admin")
def risk_flags(request):
    flags = RiskFlag.objects.filter(resolved=False).select_related(
        "student__department"
    ).order_by("-flagged_at")

    if request.user.role == "faculty":
        # Only show flags for students in this faculty's sections
        student_ids = request.user.teaching_sections.values_list("students", flat=True)
        flags = flags.filter(student_id__in=student_ids)

    return render(request, "notifications/risk_flags.html", {"flags": flags})


@role_required("faculty", "admin")
def resolve_flag(request, pk):
    flag = get_object_or_404(RiskFlag, pk=pk)
    flag.resolved = True
    flag.resolved_at = timezone.now()
    flag.resolved_by = request.user
    flag.save(update_fields=["resolved", "resolved_at", "resolved_by"])
    return redirect("notifications:risk_flags")
