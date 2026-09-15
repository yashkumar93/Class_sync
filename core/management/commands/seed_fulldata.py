"""
Seed realistic mock data for the ClassSync app's REAL users.

    python manage.py seed_fulldata [--reset]

Seeds:
  - Timetable slots for all 5 courses (Mon-Fri, realistic schedule)
  - 30 days of attendance sessions + records (75-95% attendance per student)
  - 5 assignments (some due, some upcoming)
  - Notifications (welcome + low attendance warnings)
  - FacultyAvailability (all faculty opted in)
  - 1 sample absence report
"""
import random
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Department, Course, Section, TimetableSlot, SystemConfig
from attendance.models import AttendanceSession, AttendanceRecord
from assignments.models import Assignment
from absence.models import FacultyAvailability, AbsenceReport
from notifications.models import Notification


# ── Timetable: Each course gets 3 slots/week across Mon-Sat ──────────────────
TIMETABLE = [
    # (course_index, day, period, start, end)
    # Dr. Naseer - Virtualization and Cloud (CS401)
    (0, 0, 1, time(9,  0), time(9,  50)),   # Mon P1
    (0, 2, 3, time(11, 0), time(11, 50)),   # Wed P3
    (0, 4, 2, time(10, 0), time(10, 50)),   # Fri P2

    # Dr. Madhukar - Data Structures (CS402)
    (1, 0, 2, time(10, 0), time(10, 50)),   # Mon P2
    (1, 1, 1, time(9,  0), time(9,  50)),   # Tue P1
    (1, 3, 3, time(11, 0), time(11, 50)),   # Thu P3

    # Dr. Jagadeeshwar - IoT (CS403)
    (1, 2, 1, time(9,  0), time(9,  50)),   # Wed P1  (uses course idx 1 slot workaround)
    (2, 1, 2, time(10, 0), time(10, 50)),   # Tue P2
    (2, 3, 1, time(9,  0), time(9,  50)),   # Thu P1

    # Deepak - Economics (HS401)
    (3, 0, 4, time(14, 0), time(14, 50)),   # Mon P4
    (3, 2, 2, time(10, 0), time(10, 50)),   # Wed P2
    (3, 4, 1, time(9,  0), time(9,  50)),   # Fri P1

    # Dr. Shankar - R Programming (CS404)
    (4, 1, 4, time(14, 0), time(14, 50)),   # Tue P4
    (4, 3, 2, time(10, 0), time(10, 50)),   # Thu P2
    (4, 4, 4, time(14, 0), time(14, 50)),   # Fri P4
]


class Command(BaseCommand):
    help = "Seed full mock data (timetable, attendance, assignments, notifications) for real users."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Clear attendance, assignments, notifications first.")

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Resetting mock data...")
            AttendanceRecord.objects.all().delete()
            AttendanceSession.objects.all().delete()
            Assignment.objects.all().delete()
            Notification.objects.all().delete()
            AbsenceReport.objects.all().delete()
            TimetableSlot.objects.all().delete()
            FacultyAvailability.objects.all().delete()

        self.stdout.write("Seeding full mock data...")

        # ── Ensure department + system config ─────────────────────────────────
        dept, _ = Department.objects.get_or_create(code="CSE", defaults={"name": "Computer Science & Engineering"})
        SystemConfig.objects.get_or_create(pk=1, defaults={"default_students_per_page": 15})

        # ── Gather existing users ─────────────────────────────────────────────
        faculty_usernames = ["dr.naseer", "dr.madhukar", "dr.jagadeeshwar", "deepak", "dr.shankar"]
        student_usernames = [f"23bcs{str(i).zfill(4)}" for i in range(1001, 1016)]

        faculty_users = list(User.objects.filter(username__in=faculty_usernames).order_by("username"))
        student_users = list(User.objects.filter(username__in=student_usernames).order_by("username"))

        if len(faculty_users) < 5 or len(student_users) < 15:
            self.stderr.write(self.style.ERROR(
                f"Need 5 faculty and 15 students. Found {len(faculty_users)} faculty, {len(student_users)} students. "
                "Run seed_credentials first."
            ))
            return

        # Sort faculty to match expected order
        faculty_order = {name: i for i, name in enumerate(faculty_usernames)}
        faculty_users.sort(key=lambda u: faculty_order.get(u.username, 99))

        self.stdout.write(f"  Found {len(faculty_users)} faculty, {len(student_users)} students")

        # ── Ensure courses ────────────────────────────────────────────────────
        course_data = [
            ("CS401", "Virtualization and Cloud", 3),
            ("CS402", "Data Structures and Algorithms", 4),
            ("CS403", "Internet of Things", 3),
            ("HS401", "Principles of Economics", 3),
            ("CS404", "R Programming", 3),
        ]
        courses = []
        for code, name, credits in course_data:
            c, _ = Course.objects.get_or_create(code=code, defaults={"department": dept, "name": name, "credits": credits})
            courses.append(c)

        # ── Ensure sections (all students in every course) ────────────────────
        sections = []
        rooms = ["Room 301", "Lab 201", "Room 302", "Room 105", "Lab 202"]
        for i, course in enumerate(courses):
            section, _ = Section.objects.get_or_create(
                course=course, name="A",
                defaults={"faculty": faculty_users[i], "room": rooms[i]},
            )
            section.students.set(student_users)
            sections.append(section)
        self.stdout.write(f"  {len(sections)} sections ready")

        # ── FacultyAvailability ───────────────────────────────────────────────
        for fu in faculty_users:
            FacultyAvailability.objects.get_or_create(faculty=fu, defaults={"opted_in": True})
            fu.department = dept
            fu.save(update_fields=["department"])

        # ── Timetable slots ───────────────────────────────────────────────────
        slots_created = 0
        for course_idx, day, period, start, end in TIMETABLE:
            if course_idx >= len(sections):
                continue
            _, created = TimetableSlot.objects.get_or_create(
                section=sections[course_idx], day=day, period_number=period,
                defaults={"start_time": start, "end_time": end},
            )
            if created:
                slots_created += 1
        self.stdout.write(f"  {slots_created} timetable slots created")

        # ── Attendance sessions + records (past 30 days) ──────────────────────
        today = timezone.localdate()
        
        # Build a lookup: day -> list of (timetable_slot, faculty)
        all_slots = list(TimetableSlot.objects.select_related("section__faculty").all())
        day_to_slots = {}
        for slot in all_slots:
            day_to_slots.setdefault(slot.day, []).append(slot)

        sessions_to_create = []
        for days_ago in range(1, 31):
            session_date = today - timedelta(days=days_ago)
            weekday = session_date.weekday()
            if weekday >= 6: continue
            
            slots_today = day_to_slots.get(weekday, [])
            for slot in slots_today:
                expires = timezone.make_aware(
                    timezone.datetime.combine(session_date, slot.end_time)
                )
                sessions_to_create.append(
                    AttendanceSession(
                        timetable_slot=slot,
                        date=session_date,
                        otp_code=f"{random.randint(100000, 999999)}",
                        generated_by=slot.section.faculty,
                        expires_at=expires
                    )
                )
        
        # Bulk create sessions and fetch them back (since bulk_create doesn't set IDs on Postgres < 10, though Supabase is 15+, Django might still not populate them reliably without returning fields)
        AttendanceSession.objects.bulk_create(sessions_to_create, ignore_conflicts=True)
        all_sessions = list(AttendanceSession.objects.all())
        sessions_created = len(all_sessions)
        
        records_to_create = []
        for session in all_sessions:
            for student in student_users:
                if random.random() < 0.85:
                    records_to_create.append(
                        AttendanceRecord(session=session, student=student)
                    )
                    
        AttendanceRecord.objects.bulk_create(records_to_create, ignore_conflicts=True, batch_size=2000)
        records_created = len(records_to_create)

        self.stdout.write(f"  {sessions_created} attendance sessions, {records_created} records")

        # ── Assignments ───────────────────────────────────────────────────────
        now = timezone.now()
        assignments = [
            (0, "Cloud VM Setup Lab",                  "Set up a virtual machine on AWS/GCP and document the steps.",                     -3),
            (0, "Docker Containerization Report",       "Containerize a sample web app using Docker and write a report.",                  5),
            (1, "Implement BST Operations",             "Implement insert, delete, search, and traversal for a Binary Search Tree.",       -5),
            (1, "Sorting Algorithm Analysis",           "Compare quicksort, mergesort, and heapsort with time complexity analysis.",       7),
            (2, "IoT Sensor Data Collection",           "Use an Arduino/ESP32 to collect temperature data and upload to cloud.",           10),
            (3, "Micro/Macroeconomics Case Study",      "Analyze the impact of inflation on IT sector wages. 1500 words.",                4),
            (4, "R Data Visualization Project",         "Create 5 visualizations using ggplot2 on the provided dataset.",                  -1),
            (4, "Statistical Analysis with R",          "Perform hypothesis testing on the student performance dataset.",                  8),
        ]
        for course_idx, title, desc, due_offset in assignments:
            section = sections[course_idx]
            Assignment.objects.get_or_create(
                section=section, title=title,
                defaults={
                    "description": desc,
                    "due_date": now + timedelta(days=due_offset),
                    "created_by": section.faculty,
                },
            )
        self.stdout.write(f"  {len(assignments)} assignments created")

        # ── Notifications ─────────────────────────────────────────────────────
        notif_count = 0
        # Welcome notification for all students
        for student in student_users[:5]:
            _, created = Notification.objects.get_or_create(
                recipient=student,
                message=f"Welcome to ClassSync, {student.first_name}! Your attendance and assignments are now synced.",
                notif_type="system",
            )
            if created:
                notif_count += 1

        # Low attendance warnings for random students
        warning_students = random.sample(student_users, 3)
        for student in warning_students:
            course = random.choice(courses)
            _, created = Notification.objects.get_or_create(
                recipient=student,
                message=f"Low attendance warning for {course.code}: {course.name}. Please attend regularly to avoid debarment.",
                notif_type="attendance_alert",
            )
            if created:
                notif_count += 1

        # Assignment due notifications
        for student in student_users[:8]:
            _, created = Notification.objects.get_or_create(
                recipient=student,
                message="You have assignments due in the next 7 days. Check your dashboard.",
                notif_type="assignment_due",
            )
            if created:
                notif_count += 1

        self.stdout.write(f"  {notif_count} notifications created")

        # ── Sample absence report ─────────────────────────────────────────────
        slot = TimetableSlot.objects.filter(section=sections[0]).first()
        if slot:
            tomorrow = today + timedelta(days=1)
            AbsenceReport.objects.get_or_create(
                faculty=faculty_users[0],
                timetable_slot=slot,
                date=tomorrow,
                defaults={
                    "reason": "Faculty development program",
                    "status": AbsenceReport.STATUS_PENDING,
                },
            )
            self.stdout.write("  1 absence report created")

        # ── Done ──────────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Full mock data seeded!"))
        self.stdout.write("  Students will see: attendance %, upcoming assignments, notifications")
        self.stdout.write("  Faculty will see: today's slots, section attendance, assignments")
