"""Assignments forms."""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from core.models import Section
from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["section", "title", "description", "attachment", "due_date"]
        widgets = {
            "due_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, faculty=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculty:
            self.fields["section"].queryset = faculty.teaching_sections.select_related("course").all()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "section", "title", "description",
            Row(Column("due_date"), Column("attachment")),
            Submit("submit", "Post Assignment", css_class="btn btn-primary"),
        )


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Submit Assignment", css_class="btn btn-success"))
