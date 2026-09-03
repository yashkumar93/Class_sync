"""
Seed command: populate the database with realistic demo data.

    py manage.py seed_demo [--reset]

Creates:
  - 1 Admin, 1 Department (Computer Science & Engineering)
  - 5 Courses: DS, DBMS, OS, CN, WT
  - 5 Faculty members — ALL opted-in to substitution (no permanent substitute distinction)
  - 15 Students with realistic roll numbers (22CS001–22CS015)
  - Sections linking faculty to courses and students
  - Timetable slots (Mon–Fri grid)
  - 3 sample assignments
  - 1 sample absence report (pending, broadcast ready)

--reset flag: deletes existing users, courses, sections, and slots before reseeding.
"""
import random
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Department, Course, Section, TimetableSlot, SystemConfig
from absence.models import FacultyAvailability, AbsenceReport
from assignments.models import Assignment


# ── Faculty data: (username, first_name, last_name) ─────────────────────────
FACULTY_DATA = [
    ("prof.sharma",  "Rajesh",   "Sharma"),
    ("prof.verma",   "Priya",    "Verma"),
    ("prof.nair",    "Suresh",   "Nair"),
    ("prof.gupta",   "Anita",    "Gupta"),
    ("prof.iyer",    "Karthik",  "Iyer"),
]

# ── Student data: (username, roll_number, first_name, last_name) ─────────────
STUDENT_DATA = [
    ("22cs001", "22CS001", "Aarav",    "Mehta"),
    ("22cs002", "22CS002", "Diya",     "Sharma"),
    ("22cs003", "22CS003", "Vivaan",   "Patel"),
    ("22cs004", "22CS004", "Anika",    "Singh"),
    ("22cs005", "22CS005", "Reyansh",  "Kumar"),
    ("22cs006", "22CS006", "Saanvi",   "Nair"),
    ("22cs007", "22CS007", "Aryan",    "Reddy"),
    ("22cs008", "22CS008", "Pari",     "Iyer"),
    ("22cs009", "22CS009", "Dhruv",    "Rao"),
    ("22cs010", "22CS010", "Kavya",    "Menon"),
    ("22cs011", "22CS011", "Kabir",    "Joshi"),
    ("22cs012", "22CS012", "Myra",     "Das"),
    ("22cs013", "22CS013", "Ishaan",   "Verma"),
    ("22cs014", "22CS014", "Ananya",   "Pillai"),
    ("22cs015", "22CS015", "Vihaan",   "Gupta"),
]

# ── Courses: (code, name, credits) ───────────────────────────────────────────
COURSES_DATA = [
    ("CS301", "Data Structures & Algorithms", 4),
    ("CS302", "Database Management Systems",  4),
    ("CS303", "Operating Systems",            4),
    ("CS304", "Computer Networks",            3),
    ("CS305", "Web Technologies",             3),
]

# ── Timetable schedule: (day, period, start_time, end_time) ──────────────────
# Five courses mapped to five different time slots across Mon–Fri
SLOT_SCHEDULE = [
    (0, 1, time(9,  0), time(9,  50)),   # Mon  P1  09:00–09:50
    (1, 2, time(10, 0), time(10, 50)),   # Tue  P2  10:00–10:50
    (2, 3, time(11, 0), time(11, 50)),   # Wed  P3  11:00–11:50
    (3, 1, time(9,  0), time(9,  50)),   # Thu  P1  09:00–09:50
    (4, 4, time(14, 0), time(14, 50)),   # Fri  P4  14:00–14:50
]


class Command(BaseCommand):
    help = "Seed the database with realistic demo data. Use --reset to wipe existing data first."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing users (non-superuser), courses, sections, and slots before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        self.stdout.write("Seeding demo data...")

        # ── System config ────────────────────────────────────────────────────
        config, _ = SystemConfig.objects.get_or_create(pk=1)
        config.default_students_per_page = 15
        config.save()

        # ── Department ───────────────────────────────────────────────────────
        # Handle case where old department with same name but different code exists
        dept = Department.objects.filter(name="Computer Science & Engineering").first()
        if dept is None:
            dept = Department.objects.create(code="CSE", name="Computer Science & Engineering")
        elif dept.code != "CSE":
            dept.code = "CSE"
            dept.save(update_fields=["code"])

        # ── Admin user ───────────────────────────────────────────────────────
        if not User.objects.filter(username="admin_cs").exists():
            User.objects.create_superuser(
                username="admin_cs",
                email="admin@classsync.dev",
                password="Admin@1234",
                role="admin",
                first_name="Admin",
                last_name="ClassSync",
                department=dept,
            )
            self.stdout.write("  Created admin: admin_cs / Admin@1234")

        # ── Faculty ──────────────────────────────────────────────────────────
        # ALL 5 faculty are full faculty members — no "substitute-only" distinction.
        # All are opted-in to receive substitute requests by default.
        faculty_users = []
        for username, first, last in FACULTY_DATA:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@classsync.dev",
                    "role": "faculty",
                    "department": dept,
                }
            )
            if created:
                u.set_password("Faculty@1234")
                u.save()
            # All 5 faculty can take substitute classes — no restrictions
            FacultyAvailability.objects.get_or_create(
                faculty=u,
                defaults={"opted_in": True},
            )
            faculty_users.append(u)
        self.stdout.write(f"  Created/verified {len(faculty_users)} faculty (password: Faculty@1234)")

        # ── Students ─────────────────────────────────────────────────────────
        student_users = []
        for username, roll, first, last in STUDENT_DATA:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@classsync.dev",
                    "role": "student",
                    "department": dept,
                    "roll_number": roll,
                }
            )
            if created:
                u.set_password("Student@1234")
                u.save()
            student_users.append(u)
        self.stdout.write(f"  Created/verified {len(student_users)} students (password: Student@1234)")

        # ── Courses ──────────────────────────────────────────────────────────
        courses = []
        for code, name, credits in COURSES_DATA:
            c, _ = Course.objects.get_or_create(
                code=code,
                defaults={"department": dept, "name": name, "credits": credits},
            )
            courses.append(c)
        self.stdout.write(f"  Created/verified {len(courses)} courses")

        # ── Sections (1 per course, assign faculty round-robin, 3 students each) ──
        sections = []
        rooms = ["Room A101", "Room A102", "Lab B201", "Room C301", "Lab C302"]
        for i, course in enumerate(courses):
            faculty = faculty_users[i]
            section, _ = Section.objects.get_or_create(
                course=course,
                name="A",
                defaults={"faculty": faculty, "room": rooms[i]},
            )
            # Enroll 3 students per section (15 students / 5 courses = 3 each)
            chunk = student_users[i * 3:(i + 1) * 3]
            section.students.set(chunk)
            sections.append(section)
        self.stdout.write(f"  Created/verified {len(sections)} sections with enrolled students")

        # ── Timetable slots ───────────────────────────────────────────────────
        slots_created = 0
        for i, section in enumerate(sections):
            day, period, start, end = SLOT_SCHEDULE[i]
            _, created = TimetableSlot.objects.get_or_create(
                section=section,
                day=day,
                period_number=period,
                defaults={"start_time": start, "end_time": end},
            )
            if created:
                slots_created += 1
        self.stdout.write(f"  Created {slots_created} new timetable slots")

        # ── Sample assignments ────────────────────────────────────────────────
        now = timezone.now()
        assignment_titles = [
            "Lab Exercise 1: Implement Stack & Queue",
            "Assignment 1: ER Diagram Design",
            "Lab 1: Process Scheduling Simulation",
        ]
        for i, section in enumerate(sections[:3]):
            Assignment.objects.get_or_create(
                section=section,
                title=assignment_titles[i],
                defaults={
                    "description": f"Complete the required exercises as described in the course handout.",
                    "due_date": now + timedelta(days=7 + i * 2),
                    "created_by": section.faculty,
                }
            )
        self.stdout.write("  Created/verified 3 sample assignments")

        # ── Sample absence report (broadcast workflow demo) ───────────────────
        slot = TimetableSlot.objects.filter(section=sections[0]).first()
        if slot:
            tomorrow = timezone.localdate() + timedelta(days=1)
            AbsenceReport.objects.get_or_create(
                faculty=faculty_users[0],
                timetable_slot=slot,
                date=tomorrow,
                defaults={
                    "reason": "Medical appointment (demo data)",
                    "status": AbsenceReport.STATUS_PENDING,
                }
            )
            self.stdout.write("  Created 1 sample absence report")

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\nSeed complete! Login at /login/"))
        self.stdout.write("  Admin:   admin_cs / Admin@1234")
        self.stdout.write("  Faculty: prof.sharma / Faculty@1234")
        self.stdout.write("  Student: 22cs001 / Student@1234")
        self.stdout.write("\nAll 5 faculty members can take substitute classes.")
        self.stdout.write("No faculty is restricted to substitute-only status.")

    def _reset(self):
        """Wipe users, sections, courses, and timetable slots for a clean reseed."""
        self.stdout.write(self.style.WARNING("  Resetting data..."))
        from absence.models import AbsenceReport, SubstitutionRecord, FacultyAvailability
        from attendance.models import AttendanceSession, AttendanceRecord, ThresholdAlert
        from notifications.models import Notification

        Notification.objects.all().delete()
        ThresholdAlert.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        AttendanceSession.objects.all().delete()
        AbsenceReport.objects.all().delete()
        SubstitutionRecord.objects.all().delete()
        FacultyAvailability.objects.all().delete()

        TimetableSlot.objects.all().delete()
        Section.objects.all().delete()
        Course.objects.all().delete()

        # Delete only demo users (non-superusers created by seed)
        seed_usernames = [u for u, *_ in FACULTY_DATA] + [u for u, *_ in STUDENT_DATA] + ["admin_cs"]
        User.objects.filter(username__in=seed_usernames).delete()

        self.stdout.write(self.style.WARNING("  Reset complete. Reseeding..."))
