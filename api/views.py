"""
REST API views for the ClassSync Android app.

Organised by feature module. Each view calls existing service/engine
functions from the Django apps rather than duplicating business logic.
"""
from datetime import date as date_type

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken




from core.models import User, Section, TimetableSlot, SystemConfig
from attendance.models import AttendanceSession, AttendanceRecord
from attendance.analytics import (
    get_student_attendance_summary,
    get_section_attendance_dashboard,
)
from attendance import services as attendance_services
from assignments.models import Assignment, Submission
from assignments import services as assignment_services
from absence.models import (
    AbsenceReport,
    SubstituteRequest,
    SubstitutionRecord,
    FacultyAvailability,
)
from absence.engine import (
    broadcast_substitute_requests,
    accept_substitute,
    decline_substitute,
)
from notifications.models import Notification, DeviceToken, RiskFlag
from notifications.utils import create_notification, mark_read, mark_all_read

from .permissions import IsAdmin, IsFaculty, IsStudent, IsFacultyOrAdmin
from .serializers import (
    LoginSerializer,
    UserSerializer,
    SectionSerializer,
    TimetableSlotSerializer,
    SystemConfigSerializer,
    AttendanceSessionSerializer,
    AttendanceSessionStudentSerializer,
    AttendanceSummarySerializer,
    SectionAttendanceRowSerializer,
    AssignmentSerializer,
    SubmissionSerializer,
    AbsenceReportSerializer,
    AbsenceReportCreateSerializer,
    SubstituteRequestSerializer,
    FacultyAvailabilitySerializer,
    SubstitutionRecordSerializer,
    NotificationSerializer,
    RiskFlagSerializer,
    DeviceTokenSerializer,
    TimetableCellSerializer,
    TimetableRowSerializer,
    OTPSubmitSerializer,
    GenerateOTPSerializer,
)


# ═══════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════

from supabase import create_client, Client
from django.conf import settings
import logging

_auth_logger = logging.getLogger("classsync.auth")

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate via Supabase and return JWT tokens + user profile.

    The Android app sends a username + password. Since Supabase requires an
    email address, we first look up the user's email from the local Django DB,
    then authenticate against Supabase with that email.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username_or_email = serializer.validated_data["username"]
    password = serializer.validated_data["password"]

    # --- Step 1: Resolve the login identifier to an email ---
    # If the user typed a plain username, look it up in Django to get the email.
    # If the Django user has no email yet (not yet synced), fall back to the
    # synthetic @classsync.app email that was seeded into Supabase.
    if "@" in username_or_email:
        email = username_or_email
    else:
        try:
            local_user = User.objects.get(username=username_or_email)
            # Use stored email if available, otherwise use the seeded synthetic email
            email = local_user.email if local_user.email else f"{username_or_email}@classsync.app"
        except User.DoesNotExist:
            # User not in Django DB yet — try synthetic email directly
            # (This shouldn't normally happen for seeded users)
            _auth_logger.warning("Login attempt for unknown username: %s", username_or_email)
            email = f"{username_or_email}@classsync.app"

    # --- Step 2: Authenticate against Supabase ---
    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        auth_response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        session = auth_response.session
        if not session:
            return Response(
                {"detail": "Unable to sign in with provided credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    except Exception as e:
        _auth_logger.error("Supabase sign-in failed for email %s: %s", email, e)
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # --- Step 3: Sync Supabase user → local Django user ---
    supabase_user = auth_response.user
    supa_email = supabase_user.email or ""
    user = User.objects.filter(supabase_uid=supabase_user.id).first()

    if not user and supa_email:
        # Try matching by email in Django first
        user = User.objects.filter(email=supa_email).first()
        if user:
            user.supabase_uid = supabase_user.id
            user.save(update_fields=["supabase_uid"])

    if not user and supa_email.endswith("@classsync.app"):
        # Seeded users: email = <username>@classsync.app, so extract the username
        derived_username = supa_email.replace("@classsync.app", "")
        user = User.objects.filter(username=derived_username).first()
        if user:
            user.supabase_uid = supabase_user.id
            user.email = supa_email   # Save the email so future lookups are direct
            user.save(update_fields=["supabase_uid", "email"])

    if not user:
        # Completely new user — create a minimal Django record
        user_role = supabase_user.user_metadata.get("role", User.ROLE_STUDENT) if supabase_user.user_metadata else User.ROLE_STUDENT
        user = User.objects.create_user(
            username=supa_email.split("@")[0] if supa_email else str(supabase_user.id),
            email=supa_email,
            role=user_role,
            supabase_uid=supabase_user.id,
        )

    _auth_logger.info("Successful login for user %s (pk=%s)", user.username, user.pk)
    return Response(
        {
            "refresh": session.refresh_token,
            "access": session.access_token,
            "user": UserSerializer(user).data,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Refresh JWT using a refresh token via Supabase."""
    refresh_token = request.data.get("refresh")
    if not refresh_token:
        return Response({"detail": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        auth_response = supabase.auth.refresh_session(refresh_token)
        session = auth_response.session
        if not session:
            return Response({"detail": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response({
            "access": session.access_token,
            "refresh": session.refresh_token,
        })
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return the current user's profile."""
    return Response(UserSerializer(request.user).data)


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARDS
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFaculty])
def faculty_dashboard(request):
    """Faculty dashboard aggregate data."""
    faculty = request.user
    sections = faculty.teaching_sections.select_related("course").all()

    # Today's timetable slots
    today = timezone.localdate()
    today_weekday = today.weekday()
    today_slots = []
    for section in sections:
        for slot in section.timetable_slots.filter(day=today_weekday):
            session = AttendanceSession.objects.filter(
                timetable_slot=slot, date=today
            ).first()
            today_slots.append(
                {
                    "slot": TimetableSlotSerializer(slot).data,
                    "session": (
                        AttendanceSessionSerializer(session).data if session else None
                    ),
                }
            )

    # Pending substitute requests
    pending_sub_requests = SubstituteRequest.objects.filter(
        requested_faculty=faculty,
        status=SubstituteRequest.STATUS_PENDING,
    ).select_related(
        "absence_report__faculty",
        "absence_report__timetable_slot__section__course",
    )

    # Recent absences
    recent_absences = AbsenceReport.objects.filter(faculty=faculty).order_by(
        "-created_at"
    )[:5]

    # Unread notifications
    unread = Notification.objects.filter(
        recipient=faculty, read_at__isnull=True
    ).count()

    return Response(
        {
            "sections": SectionSerializer(sections, many=True).data,
            "today": str(today),
            "today_slots": today_slots,
            "pending_sub_requests": SubstituteRequestSerializer(
                pending_sub_requests, many=True
            ).data,
            "recent_absences": AbsenceReportSerializer(
                recent_absences, many=True
            ).data,
            "unread_notifications": unread,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def student_dashboard(request):
    """Student dashboard aggregate data."""
    student = request.user
    sections = student.enrolled_sections.select_related("course", "faculty").all()
    attendance_summary = get_student_attendance_summary(student)

    # Upcoming assignments (not yet submitted, not past due)
    now = timezone.now()
    upcoming_assignments = (
        Assignment.objects.filter(
            section__in=sections,
            due_date__gte=now,
        )
        .exclude(submissions__student=student)
        .order_by("due_date")[:5]
    )

    unread = Notification.objects.filter(
        recipient=student, read_at__isnull=True
    ).count()

    return Response(
        {
            "sections": SectionSerializer(sections, many=True).data,
            "attendance_summary": AttendanceSummarySerializer(
                attendance_summary, many=True
            ).data,
            "upcoming_assignments": AssignmentSerializer(
                upcoming_assignments, many=True
            ).data,
            "unread_notifications": unread,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def admin_dashboard(request):
    """Admin dashboard stats."""
    now = timezone.now()
    thirty_days_ago = now - timezone.timedelta(days=30)

    return Response(
        {
            "total_faculty": User.objects.filter(
                role="faculty", is_active=True
            ).count(),
            "total_students": User.objects.filter(
                role="student", is_active=True
            ).count(),
            "total_sections": Section.objects.count(),
            "total_courses": Section.objects.values("course").distinct().count(),
            "self_study_count": AbsenceReport.objects.filter(
                status="self_study", date__gte=thirty_days_ago.date()
            ).count(),
            "makeup_candidates": AbsenceReport.objects.filter(
                is_makeup_candidate=True, date__gte=thirty_days_ago.date()
            ).count(),
            "active_risk_flags": RiskFlag.objects.filter(resolved=False).count(),
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# ATTENDANCE
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def generate_otp(request):
    """Generate (or regenerate) an OTP session for a timetable slot + date."""
    serializer = GenerateOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    slot = get_object_or_404(TimetableSlot, pk=serializer.validated_data["slot_id"])
    target_date = serializer.validated_data["date"]

    try:
        session = attendance_services.generate_otp(slot, target_date, request.user)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(AttendanceSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def session_detail(request, session_id):
    """Get session details (OTP, countdown, etc.)."""
    session = get_object_or_404(AttendanceSession, pk=session_id)
    if request.user.role == "faculty" and session.generated_by != request.user:
        return Response(
            {"error": "You can only view OTP sessions you generated."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(AttendanceSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def close_session(request, session_id):
    """Close an attendance session and notify absent students."""
    session = get_object_or_404(AttendanceSession, pk=session_id)
    if request.user.role == "faculty" and session.generated_by != request.user:
        return Response(
            {"error": "Only the faculty who generated this session can close it."},
            status=status.HTTP_403_FORBIDDEN,
        )

    absent_count, notified_count = attendance_services.close_session_and_notify_absences(
        session, closed_by=request.user
    )
    return Response(
        {
            "absent_count": absent_count,
            "notified_count": notified_count,
            "message": f"Session closed. {absent_count} absent, {notified_count} notified.",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def submit_otp(request):
    """Student submits OTP to mark attendance."""
    serializer = OTPSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    slot = get_object_or_404(TimetableSlot, pk=serializer.validated_data["slot_id"])
    today = timezone.localdate()

    try:
        attendance_services.mark_attendance(
            request.user, slot, today, serializer.validated_data["otp_code"]
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"message": f"Attendance marked for {slot.section.course.name}!"}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def my_attendance(request):
    """Student's per-course attendance summary."""
    summary = get_student_attendance_summary(request.user)
    return Response(AttendanceSummarySerializer(summary, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def today_sessions(request):
    """Today's classes for a student with active session info."""
    student = request.user
    today = timezone.localdate()
    today_weekday = today.weekday()
    enrolled_sections = student.enrolled_sections.all()

    result = []
    for section in enrolled_sections:
        slots = section.timetable_slots.filter(day=today_weekday)
        for slot in slots:
            session = AttendanceSession.objects.filter(
                timetable_slot=slot, date=today
            ).first()
            already_marked = False
            if session:
                already_marked = AttendanceRecord.objects.filter(
                    session=session, student=student
                ).exists()
            result.append(
                {
                    "slot": TimetableSlotSerializer(slot).data,
                    "session": (
                        AttendanceSessionStudentSerializer(session).data
                        if session
                        else None
                    ),
                    "is_active": session.is_active if session else False,
                    "already_marked": already_marked,
                }
            )

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def section_attendance_dashboard(request, section_id):
    """Per-student attendance table for a section."""
    section = get_object_or_404(Section, pk=section_id)
    if request.user.role == "faculty" and section.faculty_id != request.user.id:
        return Response(
            {"error": "You can only view attendance for your own sections."},
            status=status.HTTP_403_FORBIDDEN,
        )
    config = SystemConfig.get()
    rows = get_section_attendance_dashboard(section)

    sessions = AttendanceSession.objects.filter(
        timetable_slot__section=section
    ).order_by("-date")[:10]

    today = timezone.localdate()
    today_weekday = today.weekday()
    today_slots = section.timetable_slots.filter(day=today_weekday)

    return Response(
        {
            "section": SectionSerializer(section).data,
            "rows": SectionAttendanceRowSerializer(rows, many=True).data,
            "sessions": AttendanceSessionSerializer(sessions, many=True).data,
            "threshold": config.attendance_threshold,
            "today_slots": TimetableSlotSerializer(today_slots, many=True).data,
            "today": str(today),
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# ASSIGNMENTS
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsFaculty])
def faculty_assignments(request):
    """
    GET:  List all assignments for sections the faculty teaches.
    POST: Create a new assignment.
    """
    if request.method == "GET":
        sections = request.user.teaching_sections.all()
        assignments = Assignment.objects.filter(
            section__in=sections
        ).select_related("section__course").order_by("due_date")
        return Response(AssignmentSerializer(assignments, many=True).data)

    # POST — create assignment
    serializer = AssignmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    if serializer.validated_data["section"].faculty_id != request.user.id:
        return Response(
            {"error": "You can only post assignments for your own sections."},
            status=status.HTTP_403_FORBIDDEN,
        )
    assignment = serializer.save(created_by=request.user)

    # Notify enrolled students
    for student in assignment.section.students.filter(is_active=True):
        create_notification(
            recipient=student,
            notif_type="assignment_reminder",
            message=(
                f"New assignment posted in {assignment.section.course.name}: "
                f"'{assignment.title}' — due {assignment.due_date:%d %b %Y at %H:%M}."
            ),
            related_object_id=assignment.pk,
        )

    return Response(
        AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def submission_dashboard(request, assignment_id):
    """Per-student submission status for an assignment."""
    assignment = get_object_or_404(Assignment, pk=assignment_id)
    if request.user.role == "faculty" and assignment.created_by != request.user:
        return Response(
            {"error": "You can only view your own assignments."},
            status=status.HTTP_403_FORBIDDEN,
        )

    submitted = Submission.objects.filter(
        assignment=assignment
    ).select_related("student").order_by("student__last_name", "student__first_name")
    submitted_ids = submitted.values_list("student_id", flat=True)
    missing_students = (
        assignment.section.students.filter(is_active=True)
        .exclude(id__in=submitted_ids)
        .order_by("last_name", "first_name")
    )

    on_time = [s for s in submitted if not s.is_late]
    late = [s for s in submitted if s.is_late]

    from .serializers import UserMinimalSerializer

    return Response(
        {
            "assignment": AssignmentSerializer(assignment).data,
            "on_time": SubmissionSerializer(on_time, many=True).data,
            "late": SubmissionSerializer(late, many=True).data,
            "missing_students": UserMinimalSerializer(missing_students, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsStudent])
def student_assignments(request):
    """List assignments with submission status for the current student."""
    sections = request.user.enrolled_sections.all()
    now = timezone.now()
    assignments = Assignment.objects.filter(
        section__in=sections
    ).select_related("section__course").order_by("due_date")

    result = []
    for a in assignments:
        submission = Submission.objects.filter(
            assignment=a, student=request.user
        ).first()
        result.append(
            {
                "assignment": AssignmentSerializer(a).data,
                "submission": (
                    SubmissionSerializer(submission).data if submission else None
                ),
                "is_past_due": now > a.due_date,
                "can_resubmit": submission is not None and not a.is_past_due,
            }
        )
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsStudent])
def submit_assignment(request, assignment_id):
    """Student submits (or resubmits) an assignment file."""
    assignment = get_object_or_404(Assignment, pk=assignment_id)

    if not request.user.enrolled_sections.filter(pk=assignment.section.pk).exists():
        return Response(
            {"error": "You are not enrolled in this course."},
            status=status.HTTP_403_FORBIDDEN,
        )

    existing = Submission.objects.filter(
        assignment=assignment, student=request.user
    ).first()
    if existing and assignment.is_past_due:
        return Response(
            {"error": "Deadline has passed — this submission can no longer be changed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response(
            {"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        submission = assignment_services.submit_assignment(
            student=request.user,
            assignment=assignment,
            file=uploaded_file,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "submission": SubmissionSerializer(submission).data,
            "message": "Submission updated." if existing else "Submission received.",
        },
        status=status.HTTP_201_CREATED,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ABSENCE & SUBSTITUTIONS
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFaculty])
def report_absence(request):
    """Faculty reports an absence — triggers broadcast substitute engine."""
    serializer = AbsenceReportCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    slot = get_object_or_404(
        TimetableSlot, pk=serializer.validated_data["timetable_slot_id"]
    )
    if slot.section.faculty_id != request.user.id:
        return Response(
            {"error": "You can only report an absence for your own timetable slot."},
            status=status.HTTP_403_FORBIDDEN,
        )

    report = AbsenceReport.objects.create(
        faculty=request.user,
        timetable_slot=slot,
        date=serializer.validated_data["date"],
        reason=serializer.validated_data.get("reason", ""),
        status=AbsenceReport.STATUS_PENDING,
    )

    sent_count = broadcast_substitute_requests(report)
    if sent_count > 0:
        message = (
            f"Absence reported. Substitute request sent to {sent_count} "
            f"eligible faculty member(s)."
        )
    else:
        message = (
            "Absence reported. No eligible substitute found — "
            "period marked as Self-Study / Makeup."
        )

    return Response(
        {
            "report": AbsenceReportSerializer(report).data,
            "sent_count": sent_count,
            "message": message,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFaculty])
def my_absences(request):
    """List the faculty's own absence reports."""
    absences = (
        AbsenceReport.objects.filter(faculty=request.user)
        .prefetch_related("substitute_requests__requested_faculty")
        .select_related(
            "timetable_slot__section__course",
            "assigned_substitute",
        )
        .order_by("-date")
    )
    return Response(AbsenceReportSerializer(absences, many=True).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsFaculty])
def opt_in_status(request):
    """
    GET:  Return the faculty's substitution opt-in status.
    POST: Toggle opt-in status.
    """
    availability, _ = FacultyAvailability.objects.get_or_create(
        faculty=request.user
    )

    if request.method == "POST":
        availability.opted_in = not availability.opted_in
        availability.notes = request.data.get("notes", availability.notes)
        availability.save()

    return Response(FacultyAvailabilitySerializer(availability).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFaculty])
def pending_substitute_requests(request):
    """Pending substitute requests sent to this faculty."""
    requests_qs = SubstituteRequest.objects.filter(
        requested_faculty=request.user,
        status=SubstituteRequest.STATUS_PENDING,
    ).select_related(
        "absence_report__faculty",
        "absence_report__timetable_slot__section__course",
    )
    return Response(SubstituteRequestSerializer(requests_qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFaculty])
def accept_sub_request(request, pk):
    """Accept a substitute request."""
    sub_req = get_object_or_404(
        SubstituteRequest,
        pk=pk,
        requested_faculty=request.user,
        status=SubstituteRequest.STATUS_PENDING,
    )

    success = accept_substitute(sub_req)
    if success:
        course = sub_req.absence_report.timetable_slot.section.course.name
        date = sub_req.absence_report.date
        return Response(
            {
                "message": f"You have accepted the substitution for {course} on {date}.",
                "success": True,
            }
        )
    else:
        return Response(
            {
                "message": "This substitute slot has already been taken by another faculty member.",
                "success": False,
            },
            status=status.HTTP_409_CONFLICT,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFaculty])
def decline_sub_request(request, pk):
    """Decline a substitute request."""
    sub_req = get_object_or_404(
        SubstituteRequest,
        pk=pk,
        requested_faculty=request.user,
        status=SubstituteRequest.STATUS_PENDING,
    )

    all_declined = decline_substitute(sub_req)
    message = "You have declined the substitution request."
    if all_declined:
        message += " All eligible faculty have declined — period marked as Unassigned."

    return Response({"message": message, "all_declined": all_declined})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def substitution_history(request):
    """Substitution history log."""
    records = SubstitutionRecord.objects.select_related(
        "substitute_faculty",
        "absence_report__faculty",
        "absence_report__timetable_slot__section__course",
    ).order_by("-timestamp")

    if request.user.role == "faculty":
        records = records.filter(substitute_faculty=request.user)

    return Response(SubstitutionRecordSerializer(records, many=True).data)


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """List notifications for the current user."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-sent_at")[:50]
    return Response(NotificationSerializer(notifications, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    mark_read(pk, request.user)
    return Response({"message": "Notification marked as read."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    mark_all_read(request.user)
    return Response({"message": "All notifications marked as read."})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def risk_flags_list(request):
    """Active risk flags."""
    flags = RiskFlag.objects.filter(resolved=False).select_related(
        "student__department"
    ).order_by("-flagged_at")

    if request.user.role == "faculty":
        student_ids = request.user.teaching_sections.values_list(
            "students", flat=True
        )
        flags = flags.filter(student_id__in=student_ids)

    return Response(RiskFlagSerializer(flags, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFacultyOrAdmin])
def resolve_risk_flag(request, pk):
    """Resolve a risk flag."""
    flag = get_object_or_404(RiskFlag, pk=pk)
    if request.user.role == "faculty" and not request.user.teaching_sections.filter(
        students=flag.student, course=flag.course
    ).exists():
        return Response(
            {"error": "You can only resolve risk flags for students you teach."},
            status=status.HTTP_403_FORBIDDEN,
        )
    flag.resolved = True
    flag.resolved_at = timezone.now()
    flag.resolved_by = request.user
    flag.save(update_fields=["resolved", "resolved_at", "resolved_by"])
    return Response({"message": "Risk flag resolved."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    """Register an FCM device token for push notifications."""
    serializer = DeviceTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    token = serializer.validated_data["token"]
    platform = serializer.validated_data.get("platform", "android")

    # Upsert: update existing token's user or create new
    DeviceToken.objects.update_or_create(
        token=token,
        defaults={"user": request.user, "platform": platform},
    )
    return Response({"message": "Device token registered."}, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════════════════
# TIMETABLE
# ═══════════════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def timetable_grid(request):
    """
    Weekly timetable grid — structured JSON for the Android app.
    Returns the same grid structure as the Django template view.
    """
    user = request.user
    today = timezone.localdate()
    today_weekday = today.weekday()

    DAY_NAMES = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday",
    ]
    DAYS = list(range(5))  # Mon–Fri

    if user.role == "faculty":
        sections = list(
            user.teaching_sections.select_related("course")
            .prefetch_related("timetable_slots")
            .all()
        )
    elif user.role == "student":
        sections = list(
            user.enrolled_sections.select_related("course", "faculty")
            .prefetch_related("timetable_slots")
            .all()
        )
    else:
        sections = list(
            Section.objects.select_related("course", "faculty")
            .prefetch_related("timetable_slots")
            .all()
        )

    # Collect all weekday slots
    all_slots = []
    for section in sections:
        for slot in section.timetable_slots.all():
            if slot.day <= 4:
                all_slots.append(slot)

    # Deduplicate time bands
    time_bands = sorted(
        set((s.start_time, s.end_time) for s in all_slots),
        key=lambda x: x[0],
    )

    # Build grid
    grid = []
    for start, end in time_bands:
        band_label = f"{start:%H:%M}–{end:%H:%M}"
        row = {"band": band_label, "days": {str(d): [] for d in DAYS}}
        for slot in all_slots:
            if slot.start_time == start and slot.end_time == end and slot.day in DAYS:
                is_today = slot.day == today_weekday

                # Check for absence/substitute on today
                absence = None
                sub = None
                if is_today:
                    absence = AbsenceReport.objects.filter(
                        timetable_slot=slot, date=today
                    ).first()
                    if absence and absence.is_assigned:
                        sub = (
                            absence.assigned_substitute
                            or absence.effective_substitute
                        )

                row["days"][str(slot.day)].append(
                    {
                        "slot_id": slot.id,
                        "course_code": slot.section.course.code,
                        "course_name": slot.section.course.name,
                        "section_name": slot.section.name,
                        "faculty_name": (
                            slot.section.faculty.get_full_name()
                            if slot.section.faculty
                            else None
                        ),
                        "room": slot.section.room,
                        "is_today": is_today,
                        "is_substitute": bool(sub),
                        "substitute_name": (
                            sub.get_full_name() if sub else None
                        ),
                        "absence_status": (
                            absence.status if absence else None
                        ),
                    }
                )
        grid.append(row)

    return Response(
        {
            "grid": grid,
            "days": DAYS,
            "day_names": DAY_NAMES[:5],
            "today": str(today),
            "today_weekday": today_weekday,
        }
    )


# ── Health check ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Unauthenticated endpoint used by keep-alive pings to prevent Render free-tier sleep."""
    return Response({"status": "ok"})
