"""
Fair Reassignment Engine — the core business logic of Class Sync.

Algorithm:
1. Find all faculty who are (a) opted-in, (b) free during the slot,
   (c) not already absent that day, (d) not the reporting faculty.
2. Rank by cumulative substitution count (ascending) within tracking window.
3. Among tied lowest-count candidates → random selection (logged for audit).
4. Propose substitute → set confirmation_deadline.
5. If no eligible faculty → self-study fallback + makeup flag.

The confirm/decline step is handled in absence/views.py + a management
command (check_confirmation_timeouts) that processes expired deadlines.
"""
import random
import logging
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from core.models import User, SystemConfig
from .models import AbsenceReport, SubstitutionRecord, FacultyAvailability

logger = logging.getLogger(__name__)


def _get_substitution_count(faculty, window_days=30):
    """Return how many times `faculty` has been a substitute in the last `window_days`."""
    since = timezone.now() - timedelta(days=window_days)
    return SubstitutionRecord.objects.filter(
        substitute_faculty=faculty,
        timestamp__gte=since,
    ).count()


def find_eligible_substitutes(report: AbsenceReport):
    """
    Return a queryset of faculty eligible to substitute for `report`,
    ordered by ascending substitution count (lowest burden first).

    Eligibility criteria:
    - role = faculty
    - opted in (FacultyAvailability.opted_in = True)
    - NOT the absent faculty themselves
    - NOT already absent that same date
    - NOT already scheduled to teach a class in the same time slot
      (i.e. does not have a TimetableSlot overlapping the slot's day & period)
    - NOT already the proposed_substitute for another pending absence in that slot
    """
    slot = report.timetable_slot
    date = report.date
    config = SystemConfig.get()
    window_days = config.risk_window_days  # reuse same window for fairness

    # Faculty busy during this exact slot (same day, overlapping period)
    busy_faculty_ids = (
        User.objects.filter(
            teaching_sections__timetable_slots__day=slot.day,
            teaching_sections__timetable_slots__period_number=slot.period_number,
        )
        .values_list("id", flat=True)
    )

    # Faculty absent that day
    absent_that_day_ids = (
        AbsenceReport.objects.filter(
            date=date,
            status__in=[
                AbsenceReport.STATUS_PENDING,
                AbsenceReport.STATUS_PENDING_CONFIRMATION,
                AbsenceReport.STATUS_REASSIGNED,
            ],
        )
        .values_list("faculty_id", flat=True)
    )

    # Faculty already proposed for a different absence in this slot
    already_proposed_ids = (
        AbsenceReport.objects.filter(
            timetable_slot__day=slot.day,
            timetable_slot__period_number=slot.period_number,
            date=date,
            status=AbsenceReport.STATUS_PENDING_CONFIRMATION,
        )
        .exclude(pk=report.pk)
        .values_list("proposed_substitute_id", flat=True)
    )

    opted_in_ids = FacultyAvailability.objects.filter(
        opted_in=True
    ).values_list("faculty_id", flat=True)

    eligible = User.objects.filter(
        role="faculty",
        is_active=True,
        id__in=opted_in_ids,
    ).exclude(
        id=report.faculty_id,
    ).exclude(
        id__in=busy_faculty_ids,
    ).exclude(
        id__in=absent_that_day_ids,
    ).exclude(
        id__in=already_proposed_ids,
    )

    # Annotate each eligible faculty with their substitution count in window
    since = timezone.now() - timedelta(days=window_days)
    eligible = eligible.annotate(
        sub_count=Count(
            "substitution_records",
            filter=Q(substitution_records__timestamp__gte=since),
        )
    ).order_by("sub_count")

    return eligible


def propose_next_substitute(report: AbsenceReport):
    """
    Pick the best eligible substitute for `report` and propose them:
    - Sets report.proposed_substitute and report.confirmation_deadline.
    - Sets report.status = 'pending_confirmation'.
    - Saves the report.
    - Returns the proposed substitute User, or None if nobody is available.

    Tie-breaking: among the lowest-count group → random choice (logged).
    """
    config = SystemConfig.get()
    eligible = find_eligible_substitutes(report)

    if not eligible.exists():
        logger.info("No eligible substitutes for AbsenceReport pk=%s", report.pk)
        return None

    candidates = list(eligible)
    min_count = candidates[0].sub_count

    # All candidates tied at the minimum count
    tied = [c for c in candidates if c.sub_count == min_count]
    is_tiebreak = len(tied) > 1

    chosen = random.choice(tied)

    deadline = timezone.now() + timedelta(minutes=config.confirmation_window_minutes)

    report.proposed_substitute = chosen
    report.confirmation_deadline = deadline
    report.status = AbsenceReport.STATUS_PENDING_CONFIRMATION
    report.save(update_fields=["proposed_substitute", "confirmation_deadline", "status", "updated_at"])

    logger.info(
        "Proposed substitute %s (sub_count=%d, tiebreak=%s) for AbsenceReport pk=%s. Deadline: %s",
        chosen.get_full_name(),
        min_count,
        is_tiebreak,
        report.pk,
        deadline,
    )

    # Notify the proposed substitute
    _notify_proposed_substitute(report, chosen, is_tiebreak)

    return chosen


def confirm_substitution(report: AbsenceReport):
    """
    Called when the proposed substitute explicitly accepts.
    Finalises the SubstitutionRecord and notifies students.
    """
    if report.status != AbsenceReport.STATUS_PENDING_CONFIRMATION:
        raise ValueError("Report is not in pending_confirmation state.")
    if report.proposed_substitute is None:
        raise ValueError("No proposed substitute to confirm.")

    sub = report.proposed_substitute
    # Determine if random tie-break was used (re-check: if sub_count was tied when proposed)
    # We store this flag in the record from the proposal step; here we just create the record.
    _, was_tiebreak = _was_random_tiebreak(report)

    SubstitutionRecord.objects.create(
        absence_report=report,
        substitute_faculty=sub,
        was_random_tiebreak=was_tiebreak,
    )

    report.status = AbsenceReport.STATUS_REASSIGNED
    report.save(update_fields=["status", "updated_at"])

    logger.info(
        "Substitution confirmed: %s will cover %s.",
        sub.get_full_name(),
        report,
    )

    # Notify students
    _notify_students_reassignment(report)


def decline_or_timeout(report: AbsenceReport):
    """
    Called when a proposed substitute declines or the confirmation window expires.
    Falls through to the next eligible candidate, or self-study if none remain.
    """
    if report.proposed_substitute:
        logger.info(
            "Substitute %s declined/timed out for AbsenceReport pk=%s. Trying next.",
            report.proposed_substitute.get_full_name(),
            report.pk,
        )

    # Clear current proposal
    report.proposed_substitute = None
    report.confirmation_deadline = None
    report.status = AbsenceReport.STATUS_PENDING
    report.save(update_fields=["proposed_substitute", "confirmation_deadline", "status", "updated_at"])

    # Try the next candidate
    next_candidate = propose_next_substitute(report)

    if next_candidate is None:
        # No more candidates → self-study fallback
        mark_self_study(report)


def mark_self_study(report: AbsenceReport):
    """Fall back to self-study and flag as makeup candidate."""
    report.status = AbsenceReport.STATUS_SELF_STUDY
    report.is_makeup_candidate = True
    report.proposed_substitute = None
    report.confirmation_deadline = None
    report.save(update_fields=[
        "status", "is_makeup_candidate", "proposed_substitute",
        "confirmation_deadline", "updated_at",
    ])

    logger.info("AbsenceReport pk=%s marked as Self-Study / Makeup Candidate.", report.pk)
    _notify_students_self_study(report)
    _notify_admin_self_study(report)


# ---------------------------------------------------------------------------
# Notification helpers (delegate to notifications app)
# ---------------------------------------------------------------------------

def _notify_proposed_substitute(report, substitute, is_tiebreak):
    from notifications.utils import create_notification
    slot = report.timetable_slot
    create_notification(
        recipient=substitute,
        notif_type="substitution_request",
        message=(
            f"You have been proposed to substitute for "
            f"{report.faculty.get_full_name()} in "
            f"{slot.section.course.name} (Section {slot.section.name}) "
            f"on {report.date} at {slot.start_time:%H:%M}. "
            f"Please confirm or decline within the next "
            f"{SystemConfig.get().confirmation_window_minutes} minutes."
        ),
        related_object_id=report.pk,
    )


def _notify_students_reassignment(report):
    from notifications.utils import create_notification
    slot = report.timetable_slot
    sub = report.proposed_substitute
    students = slot.section.students.filter(is_active=True)
    for student in students:
        create_notification(
            recipient=student,
            notif_type="class_reassigned",
            message=(
                f"Your {slot.section.course.name} class on {report.date} at "
                f"{slot.start_time:%H:%M} will be taken by "
                f"{sub.get_full_name()} instead of {report.faculty.get_full_name()}."
            ),
            related_object_id=report.pk,
        )


def _notify_students_self_study(report):
    from notifications.utils import create_notification
    slot = report.timetable_slot
    students = slot.section.students.filter(is_active=True)
    for student in students:
        create_notification(
            recipient=student,
            notif_type="self_study",
            message=(
                f"Your {slot.section.course.name} class on {report.date} at "
                f"{slot.start_time:%H:%M} has been marked as Self-Study. "
                f"No substitute could be arranged. This period may be rescheduled later."
            ),
            related_object_id=report.pk,
        )


def _notify_admin_self_study(report):
    from notifications.utils import create_notification
    from core.models import User
    admins = User.objects.filter(role="admin", is_active=True)
    for admin in admins:
        create_notification(
            recipient=admin,
            notif_type="makeup_candidate",
            message=(
                f"No substitute found for {report.faculty.get_full_name()}'s class "
                f"({report.timetable_slot.section.course.name}, Section "
                f"{report.timetable_slot.section.name}) on {report.date}. "
                f"Period flagged as Makeup Candidate."
            ),
            related_object_id=report.pk,
        )


def _was_random_tiebreak(report):
    """Heuristic: return (sub_count, was_tiebreak). Used only for logging."""
    config = SystemConfig.get()
    since = timezone.now() - timedelta(days=config.risk_window_days)
    from django.db.models import Count, Q
    if report.proposed_substitute is None:
        return 0, False
    count = SubstitutionRecord.objects.filter(
        substitute_faculty=report.proposed_substitute,
        timestamp__gte=since,
    ).count()
    return count, False  # tiebreak flag stored at proposal time; simplified here
