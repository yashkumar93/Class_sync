"""
URL routing for the ClassSync REST API.
All endpoints are prefixed with /api/ (set in classsync/urls.py).
"""
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────
    path("auth/login/", views.login_view, name="login"),
    path("auth/refresh/", views.refresh_token_view, name="token_refresh"),
    path("auth/me/", views.me_view, name="me"),

    # ── Dashboards ────────────────────────────────────────────────────────
    path("dashboard/faculty/", views.faculty_dashboard, name="faculty_dashboard"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),

    # ── Attendance ────────────────────────────────────────────────────────
    path("attendance/generate-otp/", views.generate_otp, name="generate_otp"),
    path(
        "attendance/session/<int:session_id>/",
        views.session_detail,
        name="session_detail",
    ),
    path(
        "attendance/session/<int:session_id>/close/",
        views.close_session,
        name="close_session",
    ),
    path("attendance/submit-otp/", views.submit_otp, name="submit_otp"),
    path("attendance/my/", views.my_attendance, name="my_attendance"),
    path(
        "attendance/today-sessions/",
        views.today_sessions,
        name="today_sessions",
    ),
    path(
        "attendance/section/<int:section_id>/",
        views.section_attendance_dashboard,
        name="section_attendance_dashboard",
    ),

    # ── Assignments ───────────────────────────────────────────────────────
    path("assignments/", views.faculty_assignments, name="faculty_assignments"),
    path(
        "assignments/<int:assignment_id>/submissions/",
        views.submission_dashboard,
        name="submission_dashboard",
    ),
    path("assignments/student/", views.student_assignments, name="student_assignments"),
    path(
        "assignments/<int:assignment_id>/submit/",
        views.submit_assignment,
        name="submit_assignment",
    ),

    # ── Absence & Substitutions ───────────────────────────────────────────
    path("absence/report/", views.report_absence, name="report_absence"),
    path("absence/my/", views.my_absences, name="my_absences"),
    path("absence/opt-in/", views.opt_in_status, name="opt_in_status"),
    path(
        "absence/substitute-requests/",
        views.pending_substitute_requests,
        name="pending_substitute_requests",
    ),
    path(
        "absence/<int:pk>/accept/",
        views.accept_sub_request,
        name="accept_sub_request",
    ),
    path(
        "absence/<int:pk>/decline/",
        views.decline_sub_request,
        name="decline_sub_request",
    ),
    path("absence/history/", views.substitution_history, name="substitution_history"),

    # ── Notifications ─────────────────────────────────────────────────────
    path("notifications/", views.notification_list, name="notification_list"),
    path(
        "notifications/<int:pk>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/read-all/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
    path(
        "notifications/risk-flags/",
        views.risk_flags_list,
        name="risk_flags_list",
    ),
    path(
        "notifications/risk-flags/<int:pk>/resolve/",
        views.resolve_risk_flag,
        name="resolve_risk_flag",
    ),
    path(
        "notifications/device-token/",
        views.register_device_token,
        name="register_device_token",
    ),

    # ── Timetable ─────────────────────────────────────────────────────────
    path("timetable/", views.timetable_grid, name="timetable_grid"),
]
