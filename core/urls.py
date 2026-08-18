from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("faculty/dashboard/", views.FacultyDashboardView.as_view(), name="faculty_dashboard"),
    path("student/dashboard/", views.StudentDashboardView.as_view(), name="student_dashboard"),
]
