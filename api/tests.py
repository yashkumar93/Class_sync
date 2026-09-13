from datetime import time, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Course, Department, Section, TimetableSlot, User
from attendance.models import AttendanceRecord, AttendanceSession
from assignments.models import Assignment
from notifications.models import DeviceToken, Notification


class ApiAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        department = Department.objects.create(name="Computing", code="CSE")
        self.faculty = User.objects.create_user(
            username="faculty", password="password123", role="faculty"
        )
        self.other_faculty = User.objects.create_user(
            username="other", password="password123", role="faculty"
        )
        self.student = User.objects.create_user(
            username="student", password="password123", role="student"
        )
        course = Course.objects.create(department=department, code="CS101", name="Intro")
        other_course = Course.objects.create(department=department, code="CS102", name="Other")
        self.section = Section.objects.create(course=course, name="A", faculty=self.faculty)
        self.section.students.add(self.student)
        self.other_section = Section.objects.create(
            course=other_course, name="A", faculty=self.other_faculty
        )
        self.slot = TimetableSlot.objects.create(
            section=self.section, day=0, period_number=1,
            start_time=time(9), end_time=time(10),
        )
        self.other_slot = TimetableSlot.objects.create(
            section=self.other_section, day=0, period_number=1,
            start_time=time(9), end_time=time(10),
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_login_returns_tokens_and_profile(self):
        response = self.client.post(
            "/api/auth/login/", {"username": "student", "password": "password123"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["role"], "student")
        self.assertIn("access", response.data)

    def test_refresh_issues_a_new_access_token(self):
        login = self.client.post(
            "/api/auth/login/", {"username": "student", "password": "password123"}
        )
        response = self.client.post("/api/auth/refresh/", {"refresh": login.data["refresh"]})
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_jwt_from_login_authenticates_the_me_endpoint(self):
        login = self.client.post(
            "/api/auth/login/", {"username": "student", "password": "password123"}
        )
        authenticated_client = APIClient()
        authenticated_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        response = authenticated_client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "student")

    def test_student_cannot_access_faculty_dashboard(self):
        self.authenticate(self.student)
        self.assertEqual(self.client.get("/api/dashboard/faculty/").status_code, 403)

    def test_faculty_cannot_post_for_another_section(self):
        self.authenticate(self.faculty)
        response = self.client.post(
            "/api/assignments/",
            {
                "title": "Out of scope",
                "description": "",
                "section_id": self.other_section.id,
                "due_date": (timezone.now() + timedelta(days=1)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Assignment.objects.exists())

    def test_student_can_submit_valid_otp(self):
        session = AttendanceSession.objects.create(
            timetable_slot=self.slot,
            date=timezone.localdate(),
            otp_code="123456",
            generated_by=self.faculty,
            expires_at=timezone.now() + timedelta(minutes=1),
        )
        self.authenticate(self.student)
        response = self.client.post(
            "/api/attendance/submit-otp/", {"slot_id": self.slot.id, "otp_code": "123456"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AttendanceRecord.objects.filter(session=session, student=self.student).exists())

    def test_device_token_is_upserted_for_authenticated_user(self):
        self.authenticate(self.student)
        response = self.client.post(
            "/api/notifications/device-token/",
            {"token": "fcm-device-token", "platform": "android"},
        )
        self.assertEqual(response.status_code, 201)
        token = DeviceToken.objects.get(token="fcm-device-token")
        self.assertEqual(token.user, self.student)
        self.assertEqual(token.platform, "android")

    def test_device_token_can_be_reassigned_after_a_new_login(self):
        DeviceToken.objects.create(user=self.faculty, token="shared-device-token", platform="android")
        self.authenticate(self.student)
        response = self.client.post(
            "/api/notifications/device-token/",
            {"token": "shared-device-token", "platform": "android"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DeviceToken.objects.get(token="shared-device-token").user, self.student)

    def test_notification_read_is_scoped_to_the_owner(self):
        notification = Notification.objects.create(
            recipient=self.student,
            notif_type=Notification.TYPE_ANNOUNCEMENT,
            message="Private notification",
        )
        self.authenticate(self.faculty)
        response = self.client.post(f"/api/notifications/{notification.id}/read/")
        notification.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(notification.read_at)

    def test_faculty_cannot_report_absence_for_another_faculty_slot(self):
        self.authenticate(self.faculty)
        response = self.client.post(
            "/api/absence/report/",
            {"timetable_slot_id": self.other_slot.id, "date": timezone.localdate().isoformat()},
        )
        self.assertEqual(response.status_code, 403)
