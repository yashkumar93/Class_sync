"""
Absence & Broadcast Substitute Request models.
"""
from django.db import models
from django.utils import timezone
from core.models import User, TimetableSlot


class FacultyAvailability(models.Model):
    """
    Tracks each faculty member's substitution opt-in status.
    Faculty who opt out will never be proposed as substitutes.
    All 5 faculty members default to opted_in=True — no faculty is
    permanently restricted to substitute-only or non-substitute status.
    """
    faculty = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "faculty"},
        related_name="availability",
    )
    opted_in = models.BooleanField(
        default=True,
        help_text="Whether this faculty has opted in to receive substitution requests.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional: general availability notes (e.g. not available Mon mornings).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Faculty Availability"
        verbose_name_plural = "Faculty Availabilities"

    def __str__(self):
        status = "opted in" if self.opted_in else "opted out"
        return f"{self.faculty.get_full_name()} ({status})"


class AbsenceReport(models.Model):
    """
    A faculty member's report that they cannot take a scheduled class.
    Drives the broadcast reassignment engine.

    Workflow:
        PENDING → (broadcast sent to all eligible faculty)
        PENDING → ASSIGNED   (one faculty accepted)
        PENDING → UNASSIGNED (all faculty declined / none available)
        PENDING → SELF_STUDY (fallback when no eligible faculty at all)
    """
    STATUS_PENDING    = "pending"
    STATUS_ASSIGNED   = "assigned"      # a substitute has accepted
    STATUS_UNASSIGNED = "unassigned"    # all eligible faculty declined
    STATUS_SELF_STUDY = "self_study"    # no eligible faculty existed at all

    # Kept for display compat; PENDING_CONFIRMATION & REASSIGNED are legacy aliases
    STATUS_PENDING_CONFIRMATION = "pending_confirmation"  # legacy — maps to PENDING
    STATUS_REASSIGNED           = "reassigned"            # legacy — maps to ASSIGNED

    STATUS_CHOICES = [
        (STATUS_PENDING,    "Pending"),
        (STATUS_ASSIGNED,   "Assigned"),
        (STATUS_UNASSIGNED, "Unassigned — No Substitute"),
        (STATUS_SELF_STUDY, "Self-Study / Makeup Flagged"),
        # Legacy values kept so existing DB rows still display correctly
        (STATUS_PENDING_CONFIRMATION, "Pending Confirmation (legacy)"),
        (STATUS_REASSIGNED,           "Reassigned (legacy)"),
    ]

    faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "faculty"},
        related_name="absences",
    )
    timetable_slot = models.ForeignKey(
        TimetableSlot,
        on_delete=models.CASCADE,
        related_name="absence_reports",
    )
    date = models.DateField(help_text="The specific date this absence applies to.")
    reason = models.TextField(blank=True, help_text="Optional reason for absence.")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # Assigned substitute (set when a SubstituteRequest is accepted)
    assigned_substitute = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "faculty"},
        related_name="assigned_substitutions",
    )

    # --- Deprecated fields (kept for migration safety, no longer used by engine) ---
    proposed_substitute = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "faculty"},
        related_name="proposed_substitutions",
    )
    confirmation_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="DEPRECATED — kept for backward compat. Use SubstituteRequest instead.",
    )
    # ---

    is_makeup_candidate = models.BooleanField(
        default=False,
        help_text="Set True when no substitute found; flags this period for a makeup class.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        unique_together = ("faculty", "timetable_slot", "date")

    def __str__(self):
        return (
            f"{self.faculty.get_full_name()} absent on {self.date} "
            f"[{self.timetable_slot}] — {self.get_status_display()}"
        )

    @property
    def is_assigned(self):
        return self.status in (self.STATUS_ASSIGNED, self.STATUS_REASSIGNED)

    @property
    def is_pending(self):
        return self.status in (self.STATUS_PENDING, self.STATUS_PENDING_CONFIRMATION)

    @property
    def effective_substitute(self):
        """Return the confirmed substitute regardless of which field holds it."""
        return self.assigned_substitute or self.proposed_substitute


class SubstituteRequest(models.Model):
    """
    Broadcast substitute request record — one row per eligible faculty
    per AbsenceReport.

    When Faculty A reports an absence, the engine creates one SubstituteRequest
    for each of the other eligible faculty members and sends each a notification.
    The first faculty to ACCEPT locks the assignment; the remaining requests are
    automatically CANCELLED.
    """
    STATUS_PENDING   = "pending"
    STATUS_ACCEPTED  = "accepted"
    STATUS_DECLINED  = "declined"
    STATUS_CANCELLED = "cancelled"  # closed when another faculty accepted first

    STATUS_CHOICES = [
        (STATUS_PENDING,   "Pending"),
        (STATUS_ACCEPTED,  "Accepted"),
        (STATUS_DECLINED,  "Declined"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    absence_report = models.ForeignKey(
        AbsenceReport,
        on_delete=models.CASCADE,
        related_name="substitute_requests",
    )
    requested_faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "faculty"},
        related_name="received_substitute_requests",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = ("absence_report", "requested_faculty")
        verbose_name = "Substitute Request"
        verbose_name_plural = "Substitute Requests"

    def __str__(self):
        return (
            f"SubReq → {self.requested_faculty.get_full_name()} "
            f"for {self.absence_report} [{self.get_status_display()}]"
        )


class SubstitutionRecord(models.Model):
    """
    Immutable audit log of every completed substitution.
    Used for load-balancing: the engine queries the count per faculty
    within the current tracking window to pick the least-burdened substitute
    when calculating eligibility order.
    """
    absence_report = models.OneToOneField(
        AbsenceReport,
        on_delete=models.CASCADE,
        related_name="substitution_record",
    )
    substitute_faculty = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "faculty"},
        related_name="substitution_records",
    )
    was_random_tiebreak = models.BooleanField(
        default=False,
        help_text="True if this substitute was chosen via random tie-break (for audit transparency).",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.substitute_faculty.get_full_name()} covered "
            f"{self.absence_report} on {self.timestamp:%Y-%m-%d %H:%M}"
        )
