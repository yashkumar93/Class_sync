from django.contrib import admin as django_admin
from .models import User, Department, Course, Section, TimetableSlot, SystemConfig


@django_admin.register(User)
class UserAdmin(django_admin.ModelAdmin):
    list_display = ["username", "get_full_name", "email", "role", "department", "is_active"]
    list_filter = ["role", "department", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email"]


@django_admin.register(Department)
class DepartmentAdmin(django_admin.ModelAdmin):
    list_display = ["code", "name"]


@django_admin.register(Course)
class CourseAdmin(django_admin.ModelAdmin):
    list_display = ["code", "name", "department", "credits"]
    list_filter = ["department"]


@django_admin.register(Section)
class SectionAdmin(django_admin.ModelAdmin):
    list_display = ["__str__", "faculty", "room"]
    list_filter = ["course__department"]
    filter_horizontal = ["students"]


@django_admin.register(TimetableSlot)
class TimetableSlotAdmin(django_admin.ModelAdmin):
    list_display = ["__str__", "day", "period_number", "start_time", "end_time"]
    list_filter = ["day", "section__course__department"]


@django_admin.register(SystemConfig)
class SystemConfigAdmin(django_admin.ModelAdmin):
    list_display = [
        "otp_validity_seconds",
        "attendance_threshold",
        "risk_missed_submissions",
        "risk_window_days",
        "confirmation_window_minutes",
        "updated_at",
    ]
