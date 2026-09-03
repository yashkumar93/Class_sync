from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    # Faculty: generate OTP for a slot on a specific date
    path("generate/<int:slot_id>/<str:date_str>/", views.generate_otp_view, name="generate_otp"),
    # Faculty/Admin: projector display of an active session's OTP
    path("session/<int:session_id>/display/", views.session_display, name="session_display"),
    # Faculty/Admin: per-section attendance dashboard
    path("dashboard/<int:section_id>/", views.section_dashboard, name="section_dashboard"),
    # Student: mark attendance via OTP
    path("mark/", views.submit_otp, name="submit_otp"),
    # Student: personal attendance overview
    path("my/", views.my_attendance, name="my_attendance"),
    # Faculty: close session and notify absent students
    path("session/<int:session_id>/close/", views.close_session, name="close_session"),
]

