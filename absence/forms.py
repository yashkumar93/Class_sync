"""Absence app forms."""
from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from core.models import TimetableSlot
from .models import AbsenceReport


class AbsenceReportForm(forms.ModelForm):
    class Meta:
        model = AbsenceReport
        fields = ["timetable_slot", "date", "reason"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, faculty=None, **kwargs):
        super().__init__(*args, **kwargs)
        if faculty:
            # Only show timetable slots for sections this faculty teaches
            self.fields["timetable_slot"].queryset = TimetableSlot.objects.filter(
                section__faculty=faculty
            ).select_related("section__course")
        self.fields["date"].initial = timezone.localdate()
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "timetable_slot",
            "date",
            "reason",
            Submit("submit", "Report Absence", css_class="btn btn-warning"),
        )

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date < timezone.localdate():
            raise forms.ValidationError("You cannot report an absence for a past date.")
        return date
