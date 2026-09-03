"""
Broadcast Reassignment Engine — the core business logic of Class Sync.

Algorithm (Broadcast Model):
1. Faculty A reports absence.
2. Find ALL faculty who are (a) opted-in, (b) free during the slot,
   (c) not already absent that day, (d) not the reporting faculty.
3. Create ONE SubstituteRequest per eligible faculty.
4. Notify ALL eligible faculty simultaneously.
5. First faculty to ACCEPT → assigned; remaining requests CANCELLED.
6. If all DECLINE → AbsenceReport.status = UNASSIGNED.
7. If no eligible faculty at all → self-study fallback.

The accept/decline step is handled in absence/views.py.
Race condition on simultaneous acceptance is handled via select_for_update().
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from core.models import User, SystemConfig
from .models import AbsenceReport, SubstituteRequest, SubstitutionRecord, FacultyAvailability

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Eligibility Query
# ---------------------------------------------------------------------------

def find_eligible_substitutes(report: AbsenceReport):
    """
    Return a queryset of faculty eligible to substitute for `report`.

    Eligibility criteria:
    - role = faculty
    - opted in (FacultyAvailability.opted_in = True)
    - NOT the absent faculty themselves
    - NOT already absent that same date
    - NOT already scheduled to teach a class in the same time slot
    - NOT already accepted another substitute request for this same slot/date
    """
    slot = report.timetable_slot
    date = report.date
    config = SystemConfig.get()
    window_days = config.risk_window_days

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
                AbsenceReport.STATUS_ASSIGNED,
                AbsenceReport.STATUS_REASSIGNED,
            ],
        )
        .values_list("faculty_id", flat=True)
    )

    # Faculty who already accepted a substitute request for this slot/date
    already_accepted_ids = (
        SubstituteRequest.objects.filter(
            absence_report__timetable_slot__day=slot.day,
            absence_report__timetable_slot__period_number=slot.period_number,
            absence_report__date=date,
            status=SubstituteRequest.STATUS_ACCEPTED,
        )
        .exclude(absence_report=report)
        .values_list("requested_faculty_id", flat=True)
    )

    opted_in_ids = FacultyAvailability.objects.filter(
        opted_in=True
    ).values_list("faculty_id", flat=True)

    since = timezone.now() - timedelta(days=window_days)
    eligible = (
        User.objects.filter(
            role="faculty",
            is_active=True,
            id__in=opted_in_ids,
        )
        .exclude(id=report.faculty_id)
        .exclude(id__in=busy_faculty_ids)
        .exclude(id__in=absent_that_day_ids)
        .exclude(id__in=already_accepted_ids)
        .annotate(
            sub_count=Count(
                "substitution_records",
                filter=Q(substitution_records__timestamp__gte=since),
            )
        )
        .order_by("sub_count")
    )

    return eligible


# ---------------------------------------------------------------------------
# Broadcast Engine — called when an absence is reported
# ---------------------------------------------------------------------------

def broadcast_substitute_requests(report: AbsenceReport):
    """
    Broadcast substitute requests to ALL eligible faculty members simultaneously.

    - Creates one SubstituteRequest per eligible faculty.
    - Sends a notification to each.
    - If no eligible faculty exists, falls back to self-study.

    Returns the count of requests sent, or 0 if self-study fallback was used.
    """
    eligible = find_eligible_substitutes(report)

    if not eligible.exists():
        logger.info(
            "No eligible substitutes for AbsenceReport pk=%s — marking self-study.",
            report.pk,
        )
        mark_self_study(report)
        return 0

    sent_count = 0
    for faculty in eligible:
        sub_req, created = SubstituteRequest.objects.get_or_create(
            absence_report=report,
            requested_faculty=faculty,
            defaults={"status": SubstituteRequest.STATUS_PENDING},
        )
        if created:
            _notify_requested_substitute(report, faculty)
            sent_count += 1
            logger.info(
                "Substitute request sent to %s (sub_count=%s) for AbsenceReport pk=%s.",
                faculty.get_full_name(),
                faculty.sub_count,
                report.pk,
            )

    return sent_count


# ---------------------------------------------------------------------------
# Accept / Decline — called from views
# ---------------------------------------------------------------------------

@transaction.atomic
def accept_substitute(sub_request: SubstituteRequest):
    """
    Called when a faculty member accepts a substitute request.

    Uses select_for_update() on the AbsenceReport to prevent race conditions
    where two faculty attempt to accept simultaneously.

    - Sets AbsenceReport.status = ASSIGNED.
    - Sets AbsenceReport.assigned_substitute.
    - Creates a SubstitutionRecord (audit log).
    - CANCELS all other pending SubstituteRequests for the same absence.
    - Notifies students of the reassignment.

    Returns True if the assignment succeeded, False if already assigned
    by another faculty (race condition).
    """
    # Lock the absence report row
    report = (
        AbsenceReport.objects.select_for_update()
        .get(pk=sub_request.absence_report_id)
    )

    # Guard against simultaneous acceptance
    if report.is_assigned:
        logger.warning(
            "Race condition: AbsenceReport pk=%s already assigned when faculty %s tried to accept.",
            report.pk,
            sub_request.requested_faculty.get_full_name(),
        )
        return False

    faculty = sub_request.requested_faculty

    # Mark this request accepted
    sub_request.status = SubstituteRequest.STATUS_ACCEPTED
    sub_request.responded_at = timezone.now()
    sub_request.save(update_fields=["status", "responded_at"])

    # Assign on the report
    report.status = AbsenceReport.STATUS_ASSIGNED
    report.assigned_substitute = faculty
    report.save(update_fields=["status", "assigned_substitute", "updated_at"])

    # Create immutable audit record
    SubstitutionRecord.objects.get_or_create(
        absence_report=report,
        defaults={"substitute_faculty": faculty, "was_random_tiebreak": False},
    )

    # Cancel all other pending requests
    SubstituteRequest.objects.filter(
        absence_report=report,
        status=SubstituteRequest.STATUS_PENDING,
    ).exclude(pk=sub_request.pk).update(
        status=SubstituteRequest.STATUS_CANCELLED,
    )

    logger.info(
        "Substitution ASSIGNED: %s will cover AbsenceReport pk=%s.",
        faculty.get_full_name(),
        report.pk,
    )

    # Notify students
    _notify_students_reassignment(report, faculty)

    return True


@transaction.atomic
def decline_substitute(sub_request: SubstituteRequest):
    """
    Called when a faculty member declines a substitute request.

    - Sets the SubstituteRequest.status = DECLINED.
    - If ALL requests for this absence are now DECLINED → mark UNASSIGNED.

    Returns True if the absence is now fully unassigned (all declined),
    False if other pending requests still exist.
    """
    sub_request.status = SubstituteRequest.STATUS_DECLINED
    sub_request.responded_at = timezone.now()
    sub_request.save(update_fields=["status", "responded_at"])

    logger.info(
        "Substitute request declined by %s for AbsenceReport pk=%s.",
        sub_request.requested_faculty.get_full_name(),
        sub_request.absence_report_id,
    )

    # Check if all requests are now resolved (declined or cancelled)
    report = sub_request.absence_report
    still_pending = SubstituteRequest.objects.filter(
        absence_report=report,
        status=SubstituteRequest.STATUS_PENDING,
    ).exists()

    if not still_pending and not report.is_assigned:
        mark_unassigned(report)
        return True

    return False


# ---------------------------------------------------------------------------
# Status Setters
# ---------------------------------------------------------------------------

def mark_self_study(report: AbsenceReport):
    """Fall back to self-study and flag as makeup candidate."""
    report.status = AbsenceReport.STATUS_SELF_STUDY
    report.is_makeup_candidate = True
    report.assigned_substitute = None
    report.save(update_fields=[
        "status", "is_makeup_candidate", "assigned_substitute", "updated_at",
    ])

    logger.info("AbsenceReport pk=%s marked as Self-Study / Makeup Candidate.", report.pk)
    _notify_students_self_study(report)
    _notify_admin_self_study(report)


def mark_unassigned(report: AbsenceReport):
    """Mark absence as UNASSIGNED — all faculty declined."""
    report.status = AbsenceReport.STATUS_UNASSIGNED
    report.is_makeup_candidate = True
    report.save(update_fields=["status", "is_makeup_candidate", "updated_at"])

    logger.info("AbsenceReport pk=%s marked UNASSIGNED — all faculty declined.", report.pk)
    _notify_students_self_study(report)
    _notify_admin_self_study(report)


# ---------------------------------------------------------------------------
# Legacy shims — keep old call-sites from breaking
# ---------------------------------------------------------------------------

def propose_next_substitute(report: AbsenceReport):
    """
    DEPRECATED — retained for backward compatibility with any existing callers.
    Delegates to the new broadcast engine.
    """
    logger.warning(
        "propose_next_substitute() is deprecated; use broadcast_substitute_requests()."
    )
    count = broadcast_substitute_requests(report)
    if count > 0:
        # Return the first eligible faculty as a shim (callers only use this for messaging)
        return SubstituteRequest.objects.filter(
            absence_report=report,
            status=SubstituteRequest.STATUS_PENDING,
        ).select_related("requested_faculty").first()
    return None


def confirm_substitution(report: AbsenceReport):
    """DEPRECATED — use accept_substitute(sub_request) instead."""
    logger.warning("confirm_substitution() is deprecated; use accept_substitute().")
    sub_req = SubstituteRequest.objects.filter(
        absence_report=report,
        requested_faculty=report.proposed_substitute,
        status=SubstituteRequest.STATUS_PENDING,
    ).first()
    if sub_req:
        accept_substitute(sub_req)


def decline_or_timeout(report: AbsenceReport):
    """DEPRECATED — use decline_substitute(sub_request) instead."""
    logger.warning("decline_or_timeout() is deprecated; use decline_substitute().")
    if report.proposed_substitute:
        sub_req = SubstituteRequest.objects.filter(
            absence_report=report,
            requested_faculty=report.proposed_substitute,
            status=SubstituteRequest.STATUS_PENDING,
        ).first()
        if sub_req:
            decline_substitute(sub_req)


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

def _notify_requested_substitute(report, faculty):
    from notifications.utils import create_notification
    slot = report.timetable_slot
    create_notification(
        recipient=faculty,
        notif_type="substitution_request",
        message=(
            f"Substitute request: {report.faculty.get_full_name()} is absent on "
            f"{report.date} for {slot.section.course.name} "
            f"(Section {slot.section.name}) at {slot.start_time:%H:%M}. "
            f"Please accept or decline from your dashboard."
        ),
        related_object_id=report.pk,
    )


def _notify_students_reassignment(report, substitute):
    from notifications.utils import create_notification
    slot = report.timetable_slot
    students = slot.section.students.filter(is_active=True)
    for student in students:
        create_notification(
            recipient=student,
            notif_type="class_reassigned",
            message=(
                f"Your {slot.section.course.name} class on {report.date} at "
                f"{slot.start_time:%H:%M} will be taken by "
                f"{substitute.get_full_name()} instead of {report.faculty.get_full_name()}."
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
                f"{slot.start_time:%H:%M} has been marked as Self-Study / Unassigned. "
                f"No substitute could be arranged. This period may be rescheduled later."
            ),
            related_object_id=report.pk,
        )


def _notify_admin_self_study(report):
    from notifications.utils import create_notification
    from core.models import User
    admins = User.objects.filter(role="admin", is_active=True)
    slot = report.timetable_slot
    for admin in admins:
        create_notification(
            recipient=admin,
            notif_type="makeup_candidate",
            message=(
                f"No substitute assigned for {report.faculty.get_full_name()}'s class "
                f"({slot.section.course.name}, Section {slot.section.name}) "
                f"on {report.date}. Status: {report.get_status_display()}."
            ),
            related_object_id=report.pk,
        )
