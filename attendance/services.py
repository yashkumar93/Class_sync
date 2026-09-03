"""
Attendance services: OTP generation, marking, percentage calculation,
threshold alert logic, and the faculty-resolution seam that bridges
the absence/substitution system to attendance.

All business logic lives here; views.py stays thin.
"""
import random
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from core.models import SystemConfig
from absence.models import AbsenceReport, SubstitutionRecord
from .models import AttendanceSession, AttendanceRecord, ThresholdAlert


# ---------------------------------------------------------------------------
# Faculty-Resolution Seam (depends on absence app — Phase 1)
# ---------------------------------------------------------------------------

def get_effective_faculty(timetable_slot, date):
    """
    Who is actually teaching this slot on this date — original or substitute.

    If the original faculty reported absence AND it was reassigned, the
    substitute from SubstitutionRecord is the effective faculty.
    Otherwise it's the section's assigned faculty.
    """
    absence = AbsenceReport.objects.filter(
        timetable_slot=timetable_slot,
        date=date,
        status=AbsenceReport.STATUS_REASSIGNED,
    ).first()

    if absence:
        try:
            return SubstitutionRecord.objects.get(
                absence_report=absence
            ).substitute_faculty
        except SubstitutionRecord.DoesNotExist:
            pass  # Data inconsistency — fall through to original faculty

    return timetable_slot.section.faculty


def is_self_study(timetable_slot, date):
    """True if this slot on this date has been marked as self-study."""
    return AbsenceReport.objects.filter(
        timetable_slot=timetable_slot,
        date=date,
        status=AbsenceReport.STATUS_SELF_STUDY,
    ).exists()


# ---------------------------------------------------------------------------
# OTP Generation
# ---------------------------------------------------------------------------

def generate_otp(timetable_slot, date, requesting_user):
    """
    Create (or regenerate) an OTP session for a slot on a specific date.

    Guards:
    - Self-study periods cannot have attendance sessions.
    - Only the effective faculty (original or substitute) can generate.

    Returns the AttendanceSession instance.
    """
    if is_self_study(timetable_slot, date):
        raise ValidationError(
            "This period is self-study; no attendance session can be created."
        )

    effective_faculty = get_effective_faculty(timetable_slot, date)
    if requesting_user != effective_faculty and requesting_user.role != "admin":
        raise PermissionDenied(
            "Only the faculty currently assigned to this class or an admin can generate a code."
        )

    config = SystemConfig.get()
    code = f"{random.randint(0, 999999):06d}"

    session, _ = AttendanceSession.objects.update_or_create(
        timetable_slot=timetable_slot,
        date=date,
        defaults={
            "otp_code": code,
            "generated_by": requesting_user,
            "expires_at": timezone.now() + timedelta(
                seconds=config.otp_validity_seconds
            ),
        },
    )
    return session


# ---------------------------------------------------------------------------
# Mark Attendance
# ---------------------------------------------------------------------------

def mark_attendance(student, timetable_slot, date, entered_code):
    """
    Validate and record a student's attendance for a session.

    Checks (in order):
    1. An active session exists for this slot/date.
    2. The OTP has not expired.
    3. The entered code matches.
    4. The student is enrolled in the section.
    5. The student hasn't already marked attendance.

    After recording, runs threshold check.
    Returns the AttendanceRecord instance.
    """
    session = AttendanceSession.objects.filter(
        timetable_slot=timetable_slot, date=date
    ).first()

    if not session:
        raise ValidationError("No active attendance session for this class.")

    if timezone.now() > session.expires_at:
        raise ValidationError("This code has expired.")

    if entered_code != session.otp_code:
        raise ValidationError("Incorrect code.")

    # Enrollment check — Section.students is a ManyToMany
    if not timetable_slot.section.students.filter(pk=student.pk).exists():
        raise PermissionDenied("Not enrolled in this section.")

    record, created = AttendanceRecord.objects.get_or_create(
        session=session, student=student
    )
    if not created:
        raise ValidationError("Attendance already marked for this session.")

    # Threshold check against the course (not just the section)
    check_threshold(student, timetable_slot.section.course)
    return record


# ---------------------------------------------------------------------------
# Attendance Percentage (course-scoped)
# ---------------------------------------------------------------------------

def attendance_percentage(student, course):
    """
    Calculate attendance % for a student across all sections of a course
    they are enrolled in.

    Returns 100.0 if no sessions have been held yet (benefit of the doubt).
    """
    total = AttendanceSession.objects.filter(
        timetable_slot__section__course=course,
        timetable_slot__section__students=student,
    ).distinct().count()

    attended = AttendanceRecord.objects.filter(
        student=student,
        session__timetable_slot__section__course=course,
    ).count()

    return round((attended / total) * 100, 1) if total else 100.0


# ---------------------------------------------------------------------------
# Threshold Alert — resolve / reopen pattern
# ---------------------------------------------------------------------------

def check_threshold(student, course):
    """
    Check if the student's attendance in a course has crossed the threshold.

    - Below threshold + no open alert → create alert + notify.
    - Below threshold + open alert exists → do nothing (no spam).
    - At/above threshold + open alert → resolve the alert.
    """
    config = SystemConfig.get()
    pct = attendance_percentage(student, course)
    open_alert = ThresholdAlert.objects.filter(
        student=student, course=course, resolved=False
    ).first()

    if pct < config.attendance_threshold:
        if not open_alert:
            ThresholdAlert.objects.create(student=student, course=course)
            notify_threshold_alert(student, course, pct)
    else:
        if open_alert:
            open_alert.resolved = True
            open_alert.resolved_at = timezone.now()
            open_alert.save(update_fields=["resolved", "resolved_at"])


def notify_threshold_alert(student, course, pct):
    """Drop a Notification row for the student (TYPE_ATTENDANCE_ALERT)."""
    from notifications.utils import create_notification
    from core.models import SystemConfig

    config = SystemConfig.get()
    create_notification(
        recipient=student,
        notif_type="attendance_alert",
        message=(
            f"Your attendance in {course.name} has dropped to {pct:.1f}%, "
            f"which is below the required {config.attendance_threshold}%. "
            f"Please attend classes regularly to avoid academic penalties."
        ),
    )


# ---------------------------------------------------------------------------
# Close Session & Notify Absent Students (Feature 4)
# ---------------------------------------------------------------------------

def close_session_and_notify_absences(session, closed_by):
    """
    Finalise an attendance session and send absence notifications to every
    enrolled student who did NOT submit an OTP for this session.

    Rules:
    - Attendance records (present students) are NEVER modified.
    - If notification delivery fails, the absence notification record is still
      saved as FAILED delivery_status — the attendance data is unaffected.
    - Returns a tuple: (absent_students_count, notifications_sent_count)

    This function implements the PRD Feature 4 requirement:
        Faculty marks session closed
          → Attendance already recorded for present students
          → Absent students identified
          → Absence notification generated per absent student
          → Faculty can see notification status
    """
    from notifications.utils import create_notification
    from notifications.models import Notification
    import logging
    _logger = logging.getLogger(__name__)

    section = session.timetable_slot.section
    course = section.course
    date = session.date

    # Students who DID mark attendance
    present_ids = AttendanceRecord.objects.filter(
        session=session
    ).values_list("student_id", flat=True)

    # Students enrolled but NOT present
    absent_students = section.students.filter(
        is_active=True
    ).exclude(id__in=present_ids)

    absent_count = absent_students.count()
    notified_count = 0

    for student in absent_students:
        try:
            notif = create_notification(
                recipient=student,
                notif_type=Notification.TYPE_ABSENCE_MARKED,
                message=(
                    f"You were marked absent for {course.name} "
                    f"(Section {section.name}) on {date} at "
                    f"{session.timetable_slot.start_time:%H:%M}. "
                    f"Please contact your faculty if this is incorrect."
                ),
                related_object_id=session.pk,
            )
            notified_count += 1
            _logger.info(
                "Absence notification sent to student %s for session pk=%s.",
                student.pk, session.pk,
            )
        except Exception:
            _logger.warning(
                "Failed to create absence notification for student %s, session pk=%s.",
                student.pk, session.pk,
                exc_info=True,
            )
            # Attendance records are unaffected — notification failure is non-fatal

    return absent_count, notified_count

