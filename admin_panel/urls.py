from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Users
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle/", views.user_toggle_active, name="user_toggle_active"),
    # Departments
    path("departments/", views.department_list, name="department_list"),
    path("departments/create/", views.department_create, name="department_create"),
    path("departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    # Courses
    path("courses/", views.course_list, name="course_list"),
    path("courses/create/", views.course_create, name="course_create"),
    path("courses/<int:pk>/edit/", views.course_edit, name="course_edit"),
    # Sections
    path("sections/", views.section_list, name="section_list"),
    path("sections/create/", views.section_create, name="section_create"),
    path("sections/<int:pk>/edit/", views.section_edit, name="section_edit"),
    # Timetable
    path("timetable/", views.timetable_list, name="timetable_list"),
    path("timetable/create/", views.timetable_create, name="timetable_create"),
    path("timetable/<int:pk>/edit/", views.timetable_edit, name="timetable_edit"),
    path("timetable/<int:pk>/delete/", views.timetable_delete, name="timetable_delete"),
    # System Config
    path("config/", views.system_config, name="system_config"),
    # Absence Override
    path("absences/", views.absence_override_list, name="absence_override_list"),
    path("absences/<int:pk>/action/", views.absence_override_action, name="absence_override_action"),
    # Announcements
    path("announce/", views.send_announcement, name="send_announcement"),
]
