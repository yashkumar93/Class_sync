"""
Assignment services: submission logic with proper resubmission semantics,
and reminder dispatch with deduplication via ReminderLog.
"""
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from .models import Assignment, Submission, ReminderLog


# ---------------------------------------------------------------------------
# Submission Logic
# ---------------------------------------------------------------------------

def submit_assignment(student, assignment, file):
    """
    Handle assignment submission with the following rules:

    Before deadline:
      - First submission: allowed, is_late = False
      - Resubmission: allowed (update_or_create replaces the file)

    After deadline:
      - First submission: allowed, is_late = True (late but genuine)
      - Resubmission: BLOCKED (protects grading integrity)
    """
    # Enrollment check
    if not assignment.section.students.filter(pk=student.pk).exists():
        raise PermissionDenied("Not enrolled in this section.")

    existing = Submission.objects.filter(
        assignment=assignment, student=student
    ).first()
    now = timezone.now()

    if existing and now > assignment.due_date:
        raise ValidationError(
            "Deadline has passed — this submission can no longer be changed."
        )

    submission, _ = Submission.objects.update_or_create(
        assignment=assignment,
        student=student,
        defaults={
            "file": file,
            "submitted_at": now,
            "is_late": now > assignment.due_date,
        },
    )
    return submission


# ---------------------------------------------------------------------------
# Reminder Logic
# ---------------------------------------------------------------------------

REMINDER_OFFSETS = [
    (timedelta(days=3), "3_day"),
    (timedelta(days=1), "1_day"),
    (timedelta(hours=2), "2_hour"),
]

# Matches the cron cadence — run every ~10 minutes
BUFFER = timedelta(minutes=10)


def send_assignment_reminders():
    """
    Fire reminder notifications for assignments approaching their deadline.

    For each offset (3 days, 1 day, 2 hours before due):
    - Find assignments whose due_date falls within [now + offset ± BUFFER].
    - For each assignment, find enrolled students who haven't submitted yet.
    - Check ReminderLog to avoid duplicates.
    - Send notification and log it.

    Returns the number of reminders sent.
    """
    from notifications.utils import create_notification

    now = timezone.now()
    sent = 0

    for offset, label in REMINDER_OFFSETS:
        window_center = now + offset
        due_soon = Assignment.objects.filter(
            due_date__range=(window_center - BUFFER, window_center + BUFFER)
        ).select_related("section__course")

        for assignment in due_soon:
            # Students who already submitted — skip them
            already_submitted_ids = Submission.objects.filter(
                assignment=assignment
            ).values_list("student_id", flat=True)

            # Enrolled students who haven't submitted
            pending_students = assignment.section.students.filter(
                is_active=True
            ).exclude(id__in=already_submitted_ids)

            for student in pending_students:
                # Check if already sent this specific reminder
                already_sent = ReminderLog.objects.filter(
                    assignment=assignment,
                    student=student,
                    offset_label=label,
                ).exists()

                if already_sent:
                    continue

                # Human-readable label for the notification
                display_label = label.replace("_", " ").replace("day", " day").replace("hour", " hour")
                display_label = display_label.replace("  ", " ").strip()

                create_notification(
                    recipient=student,
                    notif_type="assignment_reminder",
                    message=(
                        f"Reminder: '{assignment.title}' in "
                        f"{assignment.section.course.name} is due in "
                        f"{display_label} "
                        f"({assignment.due_date:%d %b %Y at %H:%M})."
                    ),
                    related_object_id=assignment.pk,
                )

                ReminderLog.objects.create(
                    assignment=assignment,
                    student=student,
                    offset_label=label,
                )
                sent += 1

    return sent
