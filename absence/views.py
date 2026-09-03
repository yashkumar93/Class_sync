"""Absence app views — broadcast substitute workflow."""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.decorators import role_required
from core.models import TimetableSlot
from .models import AbsenceReport, FacultyAvailability, SubstituteRequest
from .engine import broadcast_substitute_requests, accept_substitute, decline_substitute
from .forms import AbsenceReportForm


# ---------------------------------------------------------------------------
# Faculty: report absence
# ---------------------------------------------------------------------------

@role_required("faculty")
def report_absence(request):
    if request.method == "POST":
        form = AbsenceReportForm(request.POST, faculty=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.faculty = request.user
            report.status = AbsenceReport.STATUS_PENDING
            report.save()

            # Broadcast to all eligible faculty simultaneously
            sent_count = broadcast_substitute_requests(report)
            if sent_count > 0:
                messages.success(
                    request,
                    f"Absence reported. Substitute request sent to {sent_count} eligible "
                    f"faculty member(s). You will be notified once someone accepts."
                )
            else:
                messages.warning(
                    request,
                    "Absence reported. No eligible substitute found — "
                    "period marked as Self-Study / Makeup."
                )
            return redirect("absence:my_absences")
    else:
        form = AbsenceReportForm(faculty=request.user)

    return render(request, "absence/report_absence.html", {"form": form})


@role_required("faculty")
def my_absences(request):
    absences = AbsenceReport.objects.filter(faculty=request.user).prefetch_related(
        "substitute_requests__requested_faculty",
    ).select_related(
        "timetable_slot__section__course", "assigned_substitute",
    ).order_by("-date")
    return render(request, "absence/my_absences.html", {"absences": absences})


# ---------------------------------------------------------------------------
# Faculty: opt-in/out
# ---------------------------------------------------------------------------

@role_required("faculty")
def opt_in_status(request):
    availability, _ = FacultyAvailability.objects.get_or_create(faculty=request.user)
    if request.method == "POST":
        availability.opted_in = not availability.opted_in
        availability.notes = request.POST.get("notes", availability.notes)
        availability.save()
        status = "opted in to" if availability.opted_in else "opted out of"
        messages.success(request, f"You have {status} substitution requests.")
        return redirect("absence:opt_in_status")
    return render(request, "absence/opt_in_status.html", {"availability": availability})


# ---------------------------------------------------------------------------
# Faculty: accept / decline a substitute request (broadcast model)
# ---------------------------------------------------------------------------

@role_required("faculty")
@require_POST
def confirm_substitute(request, pk):
    """
    Accept a substitute request.
    `pk` is the SubstituteRequest pk (not AbsenceReport pk).
    """
    sub_req = get_object_or_404(
        SubstituteRequest,
        pk=pk,
        requested_faculty=request.user,
        status=SubstituteRequest.STATUS_PENDING,
    )

    success = accept_substitute(sub_req)
    if success:
        course = sub_req.absence_report.timetable_slot.section.course.name
        date = sub_req.absence_report.date
        messages.success(
            request,
            f"You have accepted the substitution for {course} on {date}. "
            f"Students have been notified."
        )
    else:
        messages.warning(
            request,
            "This substitute slot has already been taken by another faculty member."
        )
    return redirect("core:faculty_dashboard")


@role_required("faculty")
@require_POST
def decline_substitute(request, pk):
    """
    Decline a substitute request.
    `pk` is the SubstituteRequest pk (not AbsenceReport pk).
    """
    sub_req = get_object_or_404(
        SubstituteRequest,
        pk=pk,
        requested_faculty=request.user,
        status=SubstituteRequest.STATUS_PENDING,
    )

    all_declined = decline_substitute(sub_req)
    if all_declined:
        messages.info(
            request,
            "You declined the request. All eligible faculty have now declined — "
            "the period has been marked as Unassigned."
        )
    else:
        messages.info(request, "You have declined the substitution request.")
    return redirect("core:faculty_dashboard")


# ---------------------------------------------------------------------------
# Substitution history (for admin/faculty view)
# ---------------------------------------------------------------------------

@role_required("admin", "faculty")
def substitution_history(request):
    from .models import SubstitutionRecord
    records = SubstitutionRecord.objects.select_related(
        "substitute_faculty", "absence_report__faculty",
        "absence_report__timetable_slot__section__course",
    ).order_by("-timestamp")

    if request.user.role == "faculty":
        records = records.filter(substitute_faculty=request.user)

    return render(request, "absence/substitution_history.html", {"records": records})
