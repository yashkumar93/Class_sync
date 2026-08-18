"""Assignment, Submission, and ReminderLog models."""
from django.db import models
from django.utils import timezone
from core.models import User, Section


class Assignment(models.Model):
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    attachment = models.FileField(upload_to="assignments/attachments/", blank=True, null=True)
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"role": "faculty"},
        related_name="posted_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return f"{self.title} — {self.section} (due {self.due_date:%Y-%m-%d %H:%M})"

    @property
    def is_past_due(self):
        return timezone.now() > self.due_date


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="submissions",
    )
    file = models.FileField(upload_to="submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        late_tag = " [LATE]" if self.is_late else ""
        return f"{self.student.get_full_name()} → {self.assignment.title}{late_tag}"


class ReminderLog(models.Model):
    """
    Prevents duplicate reminders — one row per (assignment, student, offset_label)
    ever sent. The management command checks this before sending.
    """
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="reminder_logs"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="reminder_logs",
    )
    offset_label = models.CharField(
        max_length=20,
        help_text="E.g. '3_day', '1_day', '2_hour'",
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("assignment", "student", "offset_label")
        ordering = ["-sent_at"]

    def __str__(self):
        return (
            f"Reminder [{self.offset_label}] → {self.student.get_full_name()} "
            f"for {self.assignment.title}"
        )
