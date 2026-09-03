"""
Core views: login, logout, role-based dashboard redirect.
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView


class LoginView(auth_views.LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("core:dashboard")


class LogoutView(auth_views.LogoutView):
    next_page = "core:login"


@login_required
def dashboard_redirect(request):
    """
    After login, send users to the appropriate role dashboard.
    """
    role = request.user.role
    if role == "admin":
        return redirect("admin_panel:dashboard")
    elif role == "faculty":
        return redirect("core:faculty_dashboard")
    else:
        return redirect("core:student_dashboard")


class FacultyDashboardView(TemplateView):
    template_name = "core/faculty_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        from django.contrib.auth.decorators import login_required
        if not request.user.is_authenticated or request.user.role != "faculty":
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from absence.models import AbsenceReport
        from attendance.models import AttendanceSession
        from assignments.models import Assignment
        from notifications.models import Notification

        ctx = super().get_context_data(**kwargs)
        faculty = self.request.user

        # Sections this faculty teaches
        sections = faculty.teaching_sections.select_related("course").all()
        ctx["sections"] = sections

        # Pending substitute requests sent to this faculty (broadcast model)
        from absence.models import SubstituteRequest
        ctx["pending_sub_requests"] = SubstituteRequest.objects.filter(
            requested_faculty=faculty,
            status=SubstituteRequest.STATUS_PENDING,
        ).select_related(
            "absence_report__faculty",
            "absence_report__timetable_slot__section__course",
        )

        # Recent absences reported by this faculty
        ctx["recent_absences"] = AbsenceReport.objects.filter(
            faculty=faculty
        ).order_by("-created_at")[:5]

        # Upcoming sessions (today's timetable slots)
        from django.utils import timezone
        today = timezone.localdate()
        today_weekday = today.weekday()
        ctx["today"] = today
        ctx["today_slots"] = sections.filter(
            timetable_slots__day=today_weekday
        ).values(
            "course__name",
            "name",
            "timetable_slots__start_time",
            "timetable_slots__end_time",
            "timetable_slots__period_number",
            "timetable_slots__id",
        ).order_by("timetable_slots__period_number")

        ctx["unread_notifications"] = Notification.objects.filter(
            recipient=faculty, read_at__isnull=True
        ).count()

        return ctx



class StudentDashboardView(TemplateView):
    template_name = "core/student_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "student":
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from attendance.analytics import get_student_attendance_summary
        from assignments.models import Assignment, Submission
        from notifications.models import Notification
        from django.utils import timezone

        ctx = super().get_context_data(**kwargs)
        student = self.request.user

        ctx["sections"] = student.enrolled_sections.select_related("course", "faculty").all()
        ctx["attendance_summary"] = get_student_attendance_summary(student)

        # Upcoming assignment deadlines
        now = timezone.now()
        ctx["upcoming_assignments"] = (
            Assignment.objects.filter(
                section__in=student.enrolled_sections.all(),
                due_date__gte=now,
            )
            .exclude(submissions__student=student)
            .order_by("due_date")[:5]
        )

        ctx["unread_notifications"] = Notification.objects.filter(
            recipient=student, read_at__isnull=True
        ).count()

        return ctx


class TimetableView(TemplateView):
    """
    Weekly timetable grid view for faculty and students.

    Faculty: shows all sections they teach.
    Students: shows all sections they are enrolled in.

    Builds a grid: { "09:00-09:50": { "Monday": slot_info, "Tuesday": None, ... } }
    """
    template_name = "core/timetable.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        if request.user.role not in ("faculty", "student", "admin"):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        from core.models import TimetableSlot, Section
        from absence.models import AbsenceReport, SubstituteRequest

        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        today_weekday = today.weekday()

        DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        DAYS = list(range(5))  # Mon–Fri

        # Collect relevant sections
        if user.role == "faculty":
            sections = list(user.teaching_sections.select_related("course").prefetch_related("timetable_slots").all())
        elif user.role == "student":
            sections = list(user.enrolled_sections.select_related("course", "faculty").prefetch_related("timetable_slots").all())
        else:
            sections = list(Section.objects.select_related("course", "faculty").prefetch_related("timetable_slots").all())

        # Collect all slots and build time bands
        all_slots = []
        for section in sections:
            for slot in section.timetable_slots.all():
                if slot.day <= 4:  # Mon–Fri only
                    all_slots.append(slot)

        # Sort and deduplicate time bands by (start_time, end_time)
        time_bands = sorted(
            set((s.start_time, s.end_time) for s in all_slots),
            key=lambda x: x[0]
        )

        # Build grid rows
        # Each row = { "band": "09:00–09:50", "days": { 0: cell_or_None, 1: ..., ... } }
        grid = []
        for start, end in time_bands:
            band_label = f"{start:%H:%M}–{end:%H:%M}"
            row = {"band": band_label, "days": {d: [] for d in DAYS}}
            for slot in all_slots:
                if slot.start_time == start and slot.end_time == end and slot.day in DAYS:
                    # Check for substitute/absence on today
                    is_today = (slot.day == today_weekday)
                    absence = None
                    sub = None
                    if is_today:
                        absence = AbsenceReport.objects.filter(
                            timetable_slot=slot,
                            date=today,
                        ).first()
                        if absence and absence.is_assigned:
                            sub = absence.assigned_substitute or absence.effective_substitute

                    row["days"][slot.day].append({
                        "slot": slot,
                        "section": slot.section,
                        "course": slot.section.course,
                        "faculty": slot.section.faculty,
                        "room": slot.section.room,
                        "is_today": is_today,
                        "is_substitute": bool(sub),
                        "substitute": sub,
                        "absence": absence,
                        "absence_status": absence.status if absence else None,
                    })
            grid.append(row)

        ctx["grid"] = grid
        ctx["days"] = DAYS
        ctx["day_names"] = DAY_NAMES
        ctx["today"] = today
        ctx["today_weekday"] = today_weekday
        ctx["sections"] = sections
        return ctx

