from django.urls import path
from . import views

app_name = "assignments"

urlpatterns = [
    path("post/", views.post_assignment, name="post_assignment"),
    path("faculty/", views.faculty_assignment_list, name="faculty_list"),
    path("<int:assignment_id>/submissions/", views.submission_dashboard, name="submission_dashboard"),
    path("student/", views.student_assignment_list, name="student_list"),
    path("<int:assignment_id>/submit/", views.submit_assignment, name="submit_assignment"),
]
