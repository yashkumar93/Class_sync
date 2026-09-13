"""
Seed real student and teacher credentials.

    py manage.py seed_credentials [--reset]

Creates:
  - 1 Department (CSE)
  - 5 Courses mapped to the real teachers
  - 15 Students (23BCS1001–23BCS1015)
  - 5 Faculty members with their course assignments
  - Sections enrolling all students in every course
"""
from django.core.management.base import BaseCommand
from core.models import User, Department, Course, Section


# ── Faculty data: (username, first_name, last_name, course_name, course_code) ─
FACULTY_DATA = [
    ("dr.naseer",   "Naseer",      "Ahmed",     "Virtualization and Cloud",        "CS401"),
    ("dr.madhukar", "Madhukar",    "",           "Data Structures and Algorithms",  "CS402"),
    ("dr.jagadeeshwar", "Jagadeeshwar", "",      "Internet of Things",             "CS403"),
    ("deepak",      "Deepak",      "",           "Principles of Economics",         "HS401"),
    ("dr.shankar",  "Shankar",     "Lingham",   "R Programming",                   "CS404"),
]

# ── Student data: (roll_number, first_name, last_name) ───────────────────────
STUDENT_DATA = [
    ("23BCS1001", "Meghana",       "Reddy"),
    ("23BCS1002", "Sathwika",      "Reddy"),
    ("23BCS1003", "Ashmith",       "Sai"),
    ("23BCS1004", "Sathwika",      "Goud"),
    ("23BCS1005", "Swetha",        "Dasari"),
    ("23BCS1006", "Sakshi",        ""),
    ("23BCS1007", "Vishnupriya",   "Gopi"),
    ("23BCS1008", "Akshay",        "Macharla"),
    ("23BCS1009", "Bhuvaneshwari", "Reddy"),
    ("23BCS1010", "Dhrutika",      "Reddy"),
    ("23BCS1011", "Laya",          "Sarala"),
    ("23BCS1012", "Greeshma",      "Reddy"),
    ("23BCS1013", "Sai Charan",    "Reddy"),
    ("23BCS1014", "Harshada",      "Reddy"),
    ("23BCS1015", "Rithvik",       "Sai"),
]


class Command(BaseCommand):
    help = "Seed real student and teacher credentials. Use --reset to clear first."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete seeded users, courses, and sections before re-seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()

        self.stdout.write("Seeding real credentials...")

        # ── Department ───────────────────────────────────────────────────
        dept, _ = Department.objects.get_or_create(
            code="CSE",
            defaults={"name": "Computer Science & Engineering"},
        )

        # ── Faculty + Courses ────────────────────────────────────────────
        faculty_users = []
        courses = []
        for username, first, last, course_name, course_code in FACULTY_DATA:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@classsync.dev",
                    "role": "faculty",
                    "department": dept,
                },
            )
            if created:
                u.set_password("Faculty@1234")
                u.save()
                self.stdout.write(f"  Created faculty: {username}")
            faculty_users.append(u)

            # Create the course taught by this faculty
            course, _ = Course.objects.get_or_create(
                code=course_code,
                defaults={
                    "department": dept,
                    "name": course_name,
                    "credits": 3,
                },
            )
            courses.append(course)

        self.stdout.write(
            self.style.SUCCESS(f"  {len(faculty_users)} faculty ready (password: Faculty@1234)")
        )

        # ── Students ─────────────────────────────────────────────────────
        student_users = []
        for roll, first, last in STUDENT_DATA:
            username = roll.lower()  # e.g. 23bcs1001
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@classsync.dev",
                    "role": "student",
                    "department": dept,
                    "roll_number": roll,
                },
            )
            if created:
                u.set_password("Student@1234")
                u.save()
                self.stdout.write(f"  Created student: {roll} — {first} {last}")
            student_users.append(u)

        self.stdout.write(
            self.style.SUCCESS(f"  {len(student_users)} students ready (password: Student@1234)")
        )

        # ── Sections (1 per course, all students enrolled in every course) ──
        for i, course in enumerate(courses):
            section, _ = Section.objects.get_or_create(
                course=course,
                name="A",
                defaults={"faculty": faculty_users[i]},
            )
            section.students.set(student_users)
        self.stdout.write(
            self.style.SUCCESS(f"  {len(courses)} sections created — all students enrolled")
        )

        # ── Summary ──────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed complete!"))
        self.stdout.write("")
        self.stdout.write("  ┌─────────────────────────────────────────────────────┐")
        self.stdout.write("  │  FACULTY CREDENTIALS          password: Faculty@1234│")
        self.stdout.write("  ├─────────────────────────────────────────────────────┤")
        for username, first, last, course_name, _ in FACULTY_DATA:
            name = f"{first} {last}".strip()
            self.stdout.write(f"  │  {username:<20} {name:<15} → {course_name}")
        self.stdout.write("  ├─────────────────────────────────────────────────────┤")
        self.stdout.write("  │  STUDENT CREDENTIALS          password: Student@1234│")
        self.stdout.write("  ├─────────────────────────────────────────────────────┤")
        for roll, first, last in STUDENT_DATA:
            name = f"{first} {last}".strip()
            self.stdout.write(f"  │  {roll.lower():<20} {roll}  {name}")
        self.stdout.write("  └─────────────────────────────────────────────────────┘")

    def _reset(self):
        """Remove data created by this command."""
        self.stdout.write(self.style.WARNING("  Resetting seeded credentials..."))
        seed_usernames = [u for u, *_ in FACULTY_DATA] + [r.lower() for r, *_ in STUDENT_DATA]
        seed_course_codes = [code for *_, code in FACULTY_DATA]

        Section.objects.filter(course__code__in=seed_course_codes).delete()
        Course.objects.filter(code__in=seed_course_codes).delete()
        User.objects.filter(username__in=seed_usernames).delete()
        self.stdout.write(self.style.WARNING("  Reset complete. Re-seeding..."))
