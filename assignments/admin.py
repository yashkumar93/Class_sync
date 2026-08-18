"""Django admin configuration for assignment models."""
from django.contrib import admin as django_admin
from .models import Assignment, Submission, ReminderLog


@django_admin.register(Assignment)
class AssignmentAdmin(django_admin.ModelAdmin):
    list_display = [
        "title", "section", "due_date", "created_by",
        "is_past_due", "created_at",
    ]
    list_filter = ["section__course", "due_date"]
    search_fields = ["title", "section__course__name", "created_by__first_name"]
    readonly_fields = ["created_at", "updated_at"]

    def is_past_due(self, obj):
        return obj.is_past_due
    is_past_due.boolean = True
    is_past_due.short_description = "Past Due?"


@django_admin.register(Submission)
class SubmissionAdmin(django_admin.ModelAdmin):
    list_display = ["student", "assignment", "submitted_at", "is_late"]
    list_filter = ["is_late", "assignment__section__course"]
    search_fields = [
        "student__first_name", "student__last_name",
        "assignment__title",
    ]
    readonly_fields = ["submitted_at"]


@django_admin.register(ReminderLog)
class ReminderLogAdmin(django_admin.ModelAdmin):
    list_display = ["assignment", "student", "offset_label", "sent_at"]
    list_filter = ["offset_label", "assignment__section__course"]
    search_fields = [
        "student__first_name", "student__last_name",
        "assignment__title",
    ]
    readonly_fields = ["sent_at"]
