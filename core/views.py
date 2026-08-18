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

        # Pending substitute confirmations for this faculty
        ctx["pending_confirmations"] = AbsenceReport.objects.filter(
            proposed_substitute=faculty, status="pending_confirmation"
        ).select_related("faculty", "timetable_slot__section__course")

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
