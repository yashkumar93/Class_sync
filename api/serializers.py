"""
DRF Serializers for the ClassSync REST API.
Mirrors every model the Android app needs.
"""
from rest_framework import serializers
from core.models import User, Department, Course, Section, TimetableSlot, SystemConfig
from attendance.models import AttendanceSession, AttendanceRecord, ThresholdAlert
from assignments.models import Assignment, Submission
from absence.models import (
    AbsenceReport,
    SubstituteRequest,
    SubstitutionRecord,
    FacultyAvailability,
)
from notifications.models import Notification, DeviceToken, RiskFlag, Announcement

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code"]


class UserSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "role",
            "phone",
            "department",
            "roll_number",
            "year_of_study",
            "is_active",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for nested use (e.g. faculty on a section)."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "role"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CourseSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Course
        fields = ["id", "code", "name", "credits", "department"]


class SectionSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    faculty = UserMinimalSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "name", "course", "faculty", "room", "student_count"]

    def get_student_count(self, obj):
        return obj.students.count()


class TimetableSlotSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    day_display = serializers.SerializerMethodField()

    class Meta:
        model = TimetableSlot
        fields = [
            "id",
            "section",
            "day",
            "day_display",
            "period_number",
            "start_time",
            "end_time",
        ]

    def get_day_display(self, obj):
        return obj.get_day_display()


class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = [
            "otp_validity_seconds",
            "attendance_threshold",
            "risk_missed_submissions",
            "risk_window_days",
            "confirmation_window_minutes",
            "default_students_per_page",
        ]


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------


class AttendanceSessionSerializer(serializers.ModelSerializer):
    slot = TimetableSlotSerializer(source="timetable_slot", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = [
            "id",
            "slot",
            "date",
            "otp_code",
            "is_active",
            "expires_at",
            "remaining_seconds",
            "created_at",
        ]

    def get_remaining_seconds(self, obj):
        from django.utils import timezone

        remaining = (obj.expires_at - timezone.now()).total_seconds()
        return max(0, int(remaining))


class AttendanceSessionStudentSerializer(serializers.ModelSerializer):
    """Session serializer for students — OTP code hidden."""

    slot = TimetableSlotSerializer(source="timetable_slot", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = AttendanceSession
        fields = ["id", "slot", "date", "is_active", "expires_at", "created_at"]


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student = UserMinimalSerializer(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ["id", "student", "marked_at"]


class AttendanceSummarySerializer(serializers.Serializer):
    """Per-course attendance summary for a student."""

    course_id = serializers.IntegerField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    attended = serializers.IntegerField()
    percentage = serializers.FloatField()
    below_threshold = serializers.BooleanField()


class SectionAttendanceRowSerializer(serializers.Serializer):
    """One row in the section attendance dashboard (per-student)."""

    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    roll_number = serializers.CharField()
    total_sessions = serializers.IntegerField()
    attended = serializers.IntegerField()
    percentage = serializers.FloatField()
    below_threshold = serializers.BooleanField()


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class AssignmentSerializer(serializers.ModelSerializer):
    section = SectionSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), source="section", write_only=True
    )
    created_by = UserMinimalSerializer(read_only=True)
    is_past_due = serializers.BooleanField(read_only=True)
    submission_count = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "description",
            "attachment",
            "due_date",
            "section",
            "section_id",
            "created_by",
            "is_past_due",
            "submission_count",
            "total_students",
            "created_at",
        ]

    def get_submission_count(self, obj):
        return obj.submissions.count()

    def get_total_students(self, obj):
        return obj.section.students.filter(is_active=True).count()


class SubmissionSerializer(serializers.ModelSerializer):
    student = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = ["id", "student", "file", "submitted_at", "is_late"]


class StudentAssignmentSerializer(serializers.Serializer):
    """Assignment with the current student's submission status."""

    assignment = AssignmentSerializer()
    submission = SubmissionSerializer(allow_null=True)
    is_past_due = serializers.BooleanField()
    can_resubmit = serializers.BooleanField()


# ---------------------------------------------------------------------------
# Absence & Substitutions
# ---------------------------------------------------------------------------


class SubstituteRequestSerializer(serializers.ModelSerializer):
    requested_faculty = UserMinimalSerializer(read_only=True)
    absence_report_id = serializers.IntegerField(
        source="absence_report.id", read_only=True
    )
    course_name = serializers.SerializerMethodField()
    section_name = serializers.SerializerMethodField()
    absent_faculty_name = serializers.SerializerMethodField()
    date = serializers.DateField(source="absence_report.date", read_only=True)
    period_info = serializers.SerializerMethodField()

    class Meta:
        model = SubstituteRequest
        fields = [
            "id",
            "absence_report_id",
            "requested_faculty",
            "status",
            "course_name",
            "section_name",
            "absent_faculty_name",
            "date",
            "period_info",
            "responded_at",
            "created_at",
        ]

    def get_course_name(self, obj):
        return obj.absence_report.timetable_slot.section.course.name

    def get_section_name(self, obj):
        return obj.absence_report.timetable_slot.section.name

    def get_absent_faculty_name(self, obj):
        return obj.absence_report.faculty.get_full_name()

    def get_period_info(self, obj):
        slot = obj.absence_report.timetable_slot
        return f"P{slot.period_number} ({slot.start_time:%H:%M}–{slot.end_time:%H:%M})"


class AbsenceReportSerializer(serializers.ModelSerializer):
    faculty = UserMinimalSerializer(read_only=True)
    timetable_slot = TimetableSlotSerializer(read_only=True)
    timetable_slot_id = serializers.PrimaryKeyRelatedField(
        queryset=TimetableSlot.objects.all(),
        source="timetable_slot",
        write_only=True,
    )
    assigned_substitute = UserMinimalSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    substitute_requests = SubstituteRequestSerializer(many=True, read_only=True)

    class Meta:
        model = AbsenceReport
        fields = [
            "id",
            "faculty",
            "timetable_slot",
            "timetable_slot_id",
            "date",
            "reason",
            "status",
            "status_display",
            "assigned_substitute",
            "is_makeup_candidate",
            "substitute_requests",
            "created_at",
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()


class FacultyAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = FacultyAvailability
        fields = ["id", "opted_in", "notes", "updated_at"]


class SubstitutionRecordSerializer(serializers.ModelSerializer):
    substitute_faculty = UserMinimalSerializer(read_only=True)
    original_faculty = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    date = serializers.DateField(source="absence_report.date", read_only=True)

    class Meta:
        model = SubstitutionRecord
        fields = [
            "id",
            "substitute_faculty",
            "original_faculty",
            "course_name",
            "date",
            "was_random_tiebreak",
            "timestamp",
        ]

    def get_original_faculty(self, obj):
        return obj.absence_report.faculty.get_full_name()

    def get_course_name(self, obj):
        return obj.absence_report.timetable_slot.section.course.name


class AbsenceReportCreateSerializer(serializers.Serializer):
    """Serializer for reporting a new absence."""

    timetable_slot_id = serializers.IntegerField()
    date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True, default="")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notif_type",
            "type_display",
            "message",
            "related_object_id",
            "sent_at",
            "read_at",
            "delivery_status",
        ]

    def get_type_display(self, obj):
        return obj.get_notif_type_display()


class RiskFlagSerializer(serializers.ModelSerializer):
    student = UserMinimalSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = RiskFlag
        fields = [
            "id",
            "student",
            "course",
            "reason",
            "attendance_pct",
            "missed_submissions",
            "flagged_at",
            "resolved",
            "resolved_at",
        ]


class DeviceTokenSerializer(serializers.ModelSerializer):
    # The endpoint intentionally upserts by token so a shared/reinstalled
    # device can move to the account that most recently signed in.
    token = serializers.CharField(max_length=255, validators=[])

    class Meta:
        model = DeviceToken
        fields = ["id", "token", "platform"]


class AnnouncementSerializer(serializers.Serializer):
    """Serializer for sending an announcement."""

    message = serializers.CharField()
    audience = serializers.ChoiceField(
        choices=[("all", "All"), ("faculty", "Faculty"), ("students", "Students")]
    )


# ---------------------------------------------------------------------------
# Dashboard aggregates
# ---------------------------------------------------------------------------


class FacultyDashboardSerializer(serializers.Serializer):
    sections = SectionSerializer(many=True)
    today_slots = serializers.ListField()
    pending_sub_requests = SubstituteRequestSerializer(many=True)
    recent_absences = AbsenceReportSerializer(many=True)
    unread_notifications = serializers.IntegerField()


class StudentDashboardSerializer(serializers.Serializer):
    sections = SectionSerializer(many=True)
    attendance_summary = AttendanceSummarySerializer(many=True)
    upcoming_assignments = AssignmentSerializer(many=True)
    unread_notifications = serializers.IntegerField()


class AdminDashboardSerializer(serializers.Serializer):
    total_faculty = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_sections = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    self_study_count = serializers.IntegerField()
    makeup_candidates = serializers.IntegerField()
    active_risk_flags = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Timetable grid
# ---------------------------------------------------------------------------


class TimetableCellSerializer(serializers.Serializer):
    """One cell in the timetable grid."""

    slot_id = serializers.IntegerField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    section_name = serializers.CharField()
    faculty_name = serializers.CharField(allow_null=True)
    room = serializers.CharField()
    is_today = serializers.BooleanField()
    is_substitute = serializers.BooleanField()
    substitute_name = serializers.CharField(allow_null=True)
    absence_status = serializers.CharField(allow_null=True)


class TimetableRowSerializer(serializers.Serializer):
    """One time-band row in the timetable."""

    band = serializers.CharField()
    days = serializers.DictField(child=serializers.ListField())


class OTPSubmitSerializer(serializers.Serializer):
    """Serializer for student OTP submission."""

    slot_id = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6)


class GenerateOTPSerializer(serializers.Serializer):
    """Serializer for faculty OTP generation."""

    slot_id = serializers.IntegerField()
    date = serializers.DateField()

