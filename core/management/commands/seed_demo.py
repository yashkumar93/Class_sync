"""
Seed command: populate the database with realistic demo data for development.

    py manage.py seed_demo

Creates:
  - 1 Admin, 1 Department, 3 Courses, 3 Sections
  - 5 Faculty members (with opt-in status)
  - 15 Students (enrolled in sections)
  - Timetable slots for Monday–Friday
  - 2 sample assignments
  - 1 sample absence report
"""
import random
from datetime import time, date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Department, Course, Section, TimetableSlot, SystemConfig
from absence.models import FacultyAvailability, AbsenceReport
from assignments.models import Assignment


FACULTY_DATA = [
    ("alice.sharma", "Alice", "Sharma"),
    ("bob.nair", "Bob", "Nair"),
    ("carol.iyer", "Carol", "Iyer"),
    ("david.menon", "David", "Menon"),
    ("eva.pillai", "Eva", "Pillai"),
]

STUDENT_DATA = [
    ("s001", "Arjun", "Kumar"), ("s002", "Priya", "Rao"), ("s003", "Rahul", "Gupta"),
    ("s004", "Sneha", "Patel"), ("s005", "Vikram", "Singh"), ("s006", "Meera", "Nair"),
    ("s007", "Aditya", "Sharma"), ("s008", "Kavita", "Menon"), ("s009", "Rohan", "Iyer"),
    ("s010", "Ananya", "Pillai"), ("s011", "Karthik", "Reddy"), ("s012", "Divya", "Kumar"),
    ("s013", "Suresh", "Das"), ("s014", "Lakshmi", "Varma"), ("s015", "Nikhil", "Joshi"),
]


class Command(BaseCommand):
    help = "Seed the database with demo data for development."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # System config
        SystemConfig.objects.get_or_create(pk=1)

        # Department
        dept, _ = Department.objects.get_or_create(code="CSE", defaults={"name": "Computer Science & Engineering"})

        # Admin user
        if not User.objects.filter(username="admin_demo").exists():
            User.objects.create_superuser(
                username="admin_demo", email="admin@classsync.dev",
                password="Admin@1234", role="admin", first_name="Admin", last_name="Demo",
                department=dept,
            )
            self.stdout.write("  Created admin: admin_demo / Admin@1234")

        # Faculty
        faculty_users = []
        for username, first, last in FACULTY_DATA:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first, "last_name": last,
                    "email": f"{username}@classsync.dev",
                    "role": "faculty", "department": dept,
                }
            )
            if created:
                u.set_password("Faculty@1234")
                u.save()
            FacultyAvailability.objects.get_or_create(faculty=u, defaults={"opted_in": True})
            faculty_users.append(u)

        self.stdout.write(f"  Created {len(faculty_users)} faculty (password: Faculty@1234)")

        # Students
        student_users = []
        for roll, first, last in STUDENT_DATA:
            u, created = User.objects.get_or_create(
                username=roll,
                defaults={
                    "first_name": first, "last_name": last,
                    "email": f"{roll}@classsync.dev",
                    "role": "student", "department": dept,
                    "roll_number": roll.upper(),
                }
            )
            if created:
                u.set_password("Student@1234")
                u.save()
            student_users.append(u)

        self.stdout.write(f"  Created {len(student_users)} students (password: Student@1234)")

        # Courses
        courses_data = [
            ("CSE101", "Introduction to Programming"),
            ("CSE201", "Data Structures"),
            ("CSE301", "Database Management Systems"),
        ]
        courses = []
        for code, name in courses_data:
            c, _ = Course.objects.get_or_create(
                code=code, defaults={"department": dept, "name": name, "credits": 4}
            )
            courses.append(c)

        # Sections (one per course, first 5 faculty, all students)
        sections = []
        for i, course in enumerate(courses):
            section, _ = Section.objects.get_or_create(
                course=course, name="A",
                defaults={"faculty": faculty_users[i], "room": f"Room {101 + i}"}
            )
            # Enroll students 1–5 in section 0, 6–10 in section 1, 11–15 in section 2
            chunk = student_users[i * 5:(i + 1) * 5]
            section.students.set(chunk)
            sections.append(section)

        self.stdout.write(f"  Created {len(sections)} sections with enrolled students")

        # Timetable slots
        slot_schedule = [
            (0, 1, time(9, 0), time(9, 50)),   # Mon P1
            (1, 2, time(10, 0), time(10, 50)),  # Tue P2
            (2, 3, time(11, 0), time(11, 50)),  # Wed P3
            (3, 1, time(9, 0), time(9, 50)),    # Thu P1
            (4, 4, time(14, 0), time(14, 50)),  # Fri P4
        ]
        slots_created = 0
        for section in sections:
            for day, period, start, end in slot_schedule:
                _, created = TimetableSlot.objects.get_or_create(
                    section=section, day=day, period_number=period,
                    defaults={"start_time": start, "end_time": end}
                )
                if created:
                    slots_created += 1

        self.stdout.write(f"  Created {slots_created} timetable slots")

        # Sample assignments
        now = timezone.now()
        for i, section in enumerate(sections):
            a, _ = Assignment.objects.get_or_create(
                section=section, title=f"Assignment {i + 1}: Foundations",
                defaults={
                    "description": "Complete the foundational exercises from Chapter 1.",
                    "due_date": now + timedelta(days=7),
                    "created_by": section.faculty,
                }
            )

        self.stdout.write("  Created 3 sample assignments")

        # Sample absence report
        slot = TimetableSlot.objects.filter(section=sections[0]).first()
        if slot:
            tomorrow = timezone.localdate() + timedelta(days=1)
            AbsenceReport.objects.get_or_create(
                faculty=faculty_users[0],
                timetable_slot=slot,
                date=tomorrow,
                defaults={"reason": "Medical appointment (demo data)", "status": "pending"}
            )
            self.stdout.write("  Created 1 sample absence report")

        self.stdout.write(self.style.SUCCESS("\nSeed complete! Login at /login/"))
        self.stdout.write("  Admin:   admin_demo / Admin@1234")
        self.stdout.write("  Faculty: alice.sharma / Faculty@1234")
        self.stdout.write("  Student: s001 / Student@1234")
