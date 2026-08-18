from django.urls import path
from . import views

app_name = "absence"

urlpatterns = [
    path("report/", views.report_absence, name="report_absence"),
    path("my/", views.my_absences, name="my_absences"),
    path("opt-in/", views.opt_in_status, name="opt_in_status"),
    path("<int:pk>/confirm/", views.confirm_substitute, name="confirm_substitute"),
    path("<int:pk>/decline/", views.decline_substitute, name="decline_substitute"),
    path("history/", views.substitution_history, name="substitution_history"),
]
