"""
Attendance app views — thin wrappers around services.py.

Faculty:
  generate_otp_view  — pick slot + date, generate session, redirect to display
  session_display    — large-text OTP + live countdown (projector view)
  section_dashboard  — per-student attendance table for a section

Student:
  submit_otp     — enter OTP code to mark attendance
  my_attendance  — personal attendance overview across enrolled courses

"""
from datetime import date as date_type

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST


from core.decorators import role_required
from core.models import SystemConfig, Section, TimetableSlot
from .models import AttendanceSession, AttendanceRecord
from .analytics import get_student_attendance_summary, get_section_attendance_dashboard
from . import services


# ---------------------------------------------------------------------------
# Faculty: Generate OTP (slot picker + creation)
# ---------------------------------------------------------------------------

@role_required("faculty", "admin")
def generate_otp_view(request, slot_id, date_str):
    """
    POST: generate (or regenerate) an OTP session for this slot/date.
    GET:  show confirmation before generating.
    """
    slot = get_object_or_404(TimetableSlot, pk=slot_id)

    try:
        target_date = date_type.fromisoformat(date_str)
    except (ValueError, TypeError):
        messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
        return redirect("core:faculty_dashboard") if request.user.role == "faculty" else redirect("admin_panel:dashboard")

    if request.method == "POST":
        try:
            session = services.generate_otp(slot, target_date, request.user)
        except ValidationError as e:
            messages.error(request, str(e.message))
            return redirect("core:faculty_dashboard") if request.user.role == "faculty" else redirect("attendance:section_dashboard", section_id=slot.section_id)
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("core:faculty_dashboard") if request.user.role == "faculty" else redirect("attendance:section_dashboard", section_id=slot.section_id)

        return redirect("attendance:session_display", session_id=session.pk)

    # GET — show the generate-OTP confirmation page
    config = SystemConfig.get()
    existing_session = AttendanceSession.objects.filter(
        timetable_slot=slot, date=target_date
    ).first()

    return render(request, "attendance/generate_otp.html", {
        "slot": slot,
        "target_date": target_date,
        "validity_seconds": config.otp_validity_seconds,
        "existing_session": existing_session,
    })


# ---------------------------------------------------------------------------
# Faculty: Session Display (projector view)
# ---------------------------------------------------------------------------

@role_required("faculty", "admin")
def session_display(request, session_id):
    """
    Large-text OTP display with live countdown — meant for projector/screen.
    Only accessible by the faculty who generated it (or admin).
    """
    session = get_object_or_404(AttendanceSession, pk=session_id)

    # Access control: only the generator or admins can view
    if request.user.role == "faculty" and session.generated_by != request.user:
        raise PermissionDenied("You can only view OTP sessions you generated.")

    config = SystemConfig.get()

    # Calculate remaining seconds for the countdown
    remaining = (session.expires_at - timezone.now()).total_seconds()
    remaining = max(0, int(remaining))

    return render(request, "attendance/otp_display.html", {
        "session": session,
        "slot": session.timetable_slot,
        "validity_seconds": config.otp_validity_seconds,
        "remaining_seconds": remaining,
    })


# ---------------------------------------------------------------------------
# Student: Submit OTP
# ---------------------------------------------------------------------------

@role_required("student")
def submit_otp(request):
    """
    Shows today's classes with active sessions.
    POST: validate and record attendance via services.mark_attendance.
    """
    today = timezone.localdate()
    student = request.user

    if request.method == "POST":
        code = request.POST.get("otp_code", "").strip()
        slot_id = request.POST.get("slot_id", "")

        if not slot_id:
            messages.error(request, "Please select a class.")
            return redirect("attendance:submit_otp")

        slot = get_object_or_404(TimetableSlot, pk=slot_id)

        try:
            services.mark_attendance(student, slot, today, code)
        except ValidationError as e:
            messages.error(request, str(e.message))
            return redirect("attendance:submit_otp")
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect("attendance:submit_otp")

        messages.success(
            request,
            f"Attendance marked for {slot.section.course.name}!"
        )
        return redirect("core:student_dashboard")

    # GET — show today's classes that have active sessions
    enrolled_sections = student.enrolled_sections.all()
    today_weekday = today.weekday()

    active_sessions = []
    for section in enrolled_sections:
        slots = section.timetable_slots.filter(day=today_weekday)
        for slot in slots:
            session = AttendanceSession.objects.filter(
                timetable_slot=slot, date=today
            ).first()
            already_marked = False
            if session:
                already_marked = AttendanceRecord.objects.filter(
                    session=session, student=student
                ).exists()
            active_sessions.append({
                "slot": slot,
                "section": section,
                "session": session,
                "is_active": session.is_active if session else False,
                "already_marked": already_marked,
            })

    return render(request, "attendance/submit_otp.html", {
        "active_sessions": active_sessions,
        "today": today,
    })


# ---------------------------------------------------------------------------
# Faculty/Admin: Section Attendance Dashboard
# ---------------------------------------------------------------------------

@role_required("faculty", "admin")
def section_dashboard(request, section_id):
    section = get_object_or_404(Section, pk=section_id)
    config = SystemConfig.get()
    rows = get_section_attendance_dashboard(section)

    sessions = AttendanceSession.objects.filter(
        timetable_slot__section=section
    ).order_by("-date")[:10]

    # Today's slots for this section (for "Generate OTP" buttons)
    today = timezone.localdate()
    today_weekday = today.weekday()
    today_slots = section.timetable_slots.filter(day=today_weekday)

    return render(request, "attendance/section_dashboard.html", {
        "section": section,
        "rows": rows,
        "sessions": sessions,
        "threshold": config.attendance_threshold,
        "today_slots": today_slots,
        "today": today,
        "students_per_page": config.default_students_per_page,
    })


# ---------------------------------------------------------------------------
# Student: My Attendance
# ---------------------------------------------------------------------------

@role_required("student")
def my_attendance(request):
    summary = get_student_attendance_summary(request.user)
    return render(request, "attendance/my_attendance.html", {"summary": summary})


# ---------------------------------------------------------------------------
# Faculty: Close Session & Notify Absent Students (Feature 4)
# ---------------------------------------------------------------------------

@role_required("faculty", "admin")
@require_POST
def close_session(request, session_id):
    """
    Faculty closes an attendance session and triggers absence notifications
    for every enrolled student who did NOT mark attendance.

    Attendance records for present students are not modified.
    Notification failure never rolls back attendance data.
    """
    session = get_object_or_404(AttendanceSession, pk=session_id)

    # Only the generator or admin can close
    if request.user.role == "faculty" and session.generated_by != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Only the faculty who generated this session can close it.")

    absent_count, notified_count = services.close_session_and_notify_absences(
        session, closed_by=request.user
    )

    messages.success(
        request,
        f"Session closed. {absent_count} student(s) were absent; "
        f"{notified_count} absence notification(s) sent."
    )
    return redirect("attendance:section_dashboard", section_id=session.timetable_slot.section_id)

