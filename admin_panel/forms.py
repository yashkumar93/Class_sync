"""Forms for the admin panel."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div
from core.models import User, Department, Course, Section, TimetableSlot, SystemConfig


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username", "first_name", "last_name", "email",
            "role", "department", "phone", "roll_number", "year_of_study",
            "password1", "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("first_name"), Column("last_name")),
            Row(Column("username"), Column("email")),
            Row(Column("role"), Column("department")),
            Row(Column("phone"), Column("roll_number"), Column("year_of_study")),
            Row(Column("password1"), Column("password2")),
            Submit("submit", "Create User", css_class="btn btn-primary"),
        )


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email",
            "role", "department", "phone", "roll_number", "year_of_study", "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Save Changes", css_class="btn btn-primary"))


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Save", css_class="btn btn-primary"))


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["department", "code", "name", "credits"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Save", css_class="btn btn-primary"))


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ["course", "name", "faculty", "students", "room"]
        widgets = {
            "students": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["faculty"].queryset = User.objects.filter(role="faculty", is_active=True)
        self.fields["students"].queryset = User.objects.filter(role="student", is_active=True)
        self.helper = FormHelper()
        self.helper.add_input(Submit("submit", "Save", css_class="btn btn-primary"))


class TimetableSlotForm(forms.ModelForm):
    class Meta:
        model = TimetableSlot
        fields = ["section", "day", "period_number", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "section",
            Row(Column("day"), Column("period_number")),
            Row(Column("start_time"), Column("end_time")),
            Submit("submit", "Save", css_class="btn btn-primary"),
        )


class SystemConfigForm(forms.ModelForm):
    class Meta:
        model = SystemConfig
        fields = [
            "otp_validity_seconds", "attendance_threshold",
            "risk_missed_submissions", "risk_window_days",
            "confirmation_window_minutes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("otp_validity_seconds"), Column("attendance_threshold")),
            Row(Column("risk_missed_submissions"), Column("risk_window_days")),
            "confirmation_window_minutes",
            Submit("submit", "Save Configuration", css_class="btn btn-primary"),
        )


class AnnouncementForm(forms.Form):
    AUDIENCE_CHOICES = [
        ("all", "Everyone"),
        ("faculty", "Faculty only"),
        ("students", "Students only"),
    ]
    audience = forms.ChoiceField(choices=AUDIENCE_CHOICES)
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "audience",
            "message",
            Submit("submit", "Send Announcement", css_class="btn btn-primary"),
        )
