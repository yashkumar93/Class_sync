"""Notification, DeviceToken, Announcement, and RiskFlag models."""
from django.db import models
from core.models import User, Section, Course


class Notification(models.Model):
    TYPE_SUBSTITUTION_REQUEST = "substitution_request"
    TYPE_CLASS_REASSIGNED = "class_reassigned"
    TYPE_SELF_STUDY = "self_study"
    TYPE_MAKEUP_CANDIDATE = "makeup_candidate"
    TYPE_ANNOUNCEMENT = "announcement"
    TYPE_ASSIGNMENT_REMINDER = "assignment_reminder"
    TYPE_ATTENDANCE_ALERT = "attendance_alert"
    TYPE_RISK_FLAG = "risk_flag"
    TYPE_ABSENCE_MARKED = "absence_marked"   # student marked absent by faculty

    TYPE_CHOICES = [
        (TYPE_SUBSTITUTION_REQUEST, "Substitution Request"),
        (TYPE_CLASS_REASSIGNED, "Class Reassigned"),
        (TYPE_SELF_STUDY, "Self-Study Fallback"),
        (TYPE_MAKEUP_CANDIDATE, "Makeup Candidate Flagged"),
        (TYPE_ANNOUNCEMENT, "Announcement"),
        (TYPE_ASSIGNMENT_REMINDER, "Assignment Reminder"),
        (TYPE_ATTENDANCE_ALERT, "Attendance Alert"),
        (TYPE_RISK_FLAG, "Early-Warning Flag"),
        (TYPE_ABSENCE_MARKED, "Absence Marked"),
    ]

    # Delivery status for tracking the notification pipeline
    DELIVERY_PENDING   = "pending"
    DELIVERY_SENT      = "sent"
    DELIVERY_DELIVERED = "delivered"
    DELIVERY_READ      = "read"
    DELIVERY_FAILED    = "failed"
    DELIVERY_CHOICES = [
        (DELIVERY_PENDING,   "Pending"),
        (DELIVERY_SENT,      "Sent"),
        (DELIVERY_DELIVERED, "Delivered"),
        (DELIVERY_READ,      "Read"),
        (DELIVERY_FAILED,    "Failed"),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    notif_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField()
    related_object_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="PK of the related object (AbsenceReport, Assignment, etc.)"
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(
        max_length=15,
        choices=DELIVERY_CHOICES,
        default=DELIVERY_PENDING,
        help_text="Tracks the delivery pipeline: PENDING → SENT → DELIVERED → READ / FAILED",
    )

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        read_status = "read" if self.read_at else "unread"
        return f"[{self.get_notif_type_display()}] → {self.recipient.username} ({read_status})"

    @property
    def is_read(self):
        return self.read_at is not None


class DeviceToken(models.Model):
    """
    Stores FCM device tokens for push notification delivery.
    A user can have multiple tokens (web, Android, iOS).
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="device_tokens"
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(
        max_length=20, blank=True,
        help_text="Device platform: 'web', 'android', 'ios'"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.platform or 'unknown'} ({self.token[:12]}…)"


class Announcement(models.Model):
    """
    Faculty/admin announcements with scope control.
    Section-scoped: only that section's students receive it.
    Institution-wide: all active users receive it.
    """
    SCOPE_SECTION = "section"
    SCOPE_INSTITUTION = "institution"
    SCOPE_CHOICES = [
        (SCOPE_SECTION, "Section"),
        (SCOPE_INSTITUTION, "Institution-wide"),
    ]

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_announcements"
    )
    scope = models.CharField(max_length=15, choices=SCOPE_CHOICES)
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, null=True, blank=True,
        related_name="announcements",
        help_text="Required for section-scoped announcements.",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        if self.scope == self.SCOPE_SECTION and self.section:
            return f"Announcement → {self.section} by {self.sender.get_full_name()}"
        return f"Announcement → Institution by {self.sender.get_full_name()}"


class RiskFlag(models.Model):
    """Early-warning flag for a student showing at-risk behaviour."""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="risk_flags",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="risk_flags",
        help_text="The specific course this flag relates to.",
    )
    reason = models.TextField(help_text="Human-readable explanation: attendance %, missed submissions count, etc.")
    attendance_pct = models.FloatField(null=True, blank=True, help_text="Attendance % at time of flagging.")
    missed_submissions = models.PositiveSmallIntegerField(default=0)
    flagged_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_flags",
    )

    class Meta:
        ordering = ["-flagged_at"]

    def __str__(self):
        status = "resolved" if self.resolved else "active"
        course_label = f" ({self.course.code})" if self.course else ""
        return f"RiskFlag: {self.student.get_full_name()}{course_label} [{status}] @ {self.flagged_at:%Y-%m-%d}"
