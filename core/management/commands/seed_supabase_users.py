"""
Management command: seed_supabase_users

Creates user accounts in Supabase Auth directly from hardcoded seed data
using the admin API (requires service_role key).

This command does NOT query the local Django database, so it works even when
the local machine cannot reach the Supabase PostgreSQL port. The Django ↔
Supabase UID linking happens automatically at first login on the live server.

Usage:
    python manage.py seed_supabase_users
"""
import os
import django
from django.conf import settings
from django.core.management.base import BaseCommand
from supabase import create_client, Client

# ── Seed data ────────────────────────────────────────────────────────────────
EMAIL_DOMAIN = "classsync.app"

FACULTY = [
    ("dr.naseer",       "faculty", "Faculty@1234"),
    ("dr.madhukar",     "faculty", "Faculty@1234"),
    ("dr.jagadeeshwar", "faculty", "Faculty@1234"),
    ("deepak",          "faculty", "Faculty@1234"),
    ("dr.shankar",      "faculty", "Faculty@1234"),
]

STUDENTS = [
    ("23bcs1001", "student", "Student@1234"),
    ("23bcs1002", "student", "Student@1234"),
    ("23bcs1003", "student", "Student@1234"),
    ("23bcs1004", "student", "Student@1234"),
    ("23bcs1005", "student", "Student@1234"),
    ("23bcs1006", "student", "Student@1234"),
    ("23bcs1007", "student", "Student@1234"),
    ("23bcs1008", "student", "Student@1234"),
    ("23bcs1009", "student", "Student@1234"),
    ("23bcs1010", "student", "Student@1234"),
    ("23bcs1011", "student", "Student@1234"),
    ("23bcs1012", "student", "Student@1234"),
    ("23bcs1013", "student", "Student@1234"),
    ("23bcs1014", "student", "Student@1234"),
    ("23bcs1015", "student", "Student@1234"),
]


class Command(BaseCommand):
    help = "Seed ClassSync users into Supabase Auth (no local DB access needed)."

    def handle(self, *args, **options):
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_ROLE_KEY
        if not url or not key:
            self.stderr.write(self.style.ERROR(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env / environment."
            ))
            return

        supabase: Client = create_client(url, key)
        all_users = FACULTY + STUDENTS

        # Fetch existing Supabase users once to avoid duplicate checks
        self.stdout.write("Fetching existing Supabase users...")
        try:
            existing = supabase.auth.admin.list_users()
            existing_emails = {u.email for u in existing if hasattr(u, "email") and u.email}
            self.stdout.write(f"Found {len(existing_emails)} existing Supabase accounts.\n")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to list Supabase users: {e}"))
            existing_emails = set()

        created = 0
        skipped = 0
        errors = 0

        for username, role, password in all_users:
            email = f"{username}@{EMAIL_DOMAIN}"

            if email in existing_emails:
                self.stdout.write(self.style.WARNING(
                    f"  SKIP  {username} ({email}) - already in Supabase"
                ))
                skipped += 1
                continue

            try:
                res = supabase.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "username": username,
                        "role": role,
                    },
                })
                supa_user = res.user
                if not supa_user:
                    self.stderr.write(self.style.ERROR(
                        f"  FAIL  {username} - Supabase returned no user object"
                    ))
                    errors += 1
                    continue

                self.stdout.write(self.style.SUCCESS(
                    f"  OK    {username} ({email}) uid={supa_user.id}"
                ))
                created += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"  FAIL  {username} - {e}"
                ))
                errors += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done!  Created: {created}  |  Skipped: {skipped}  |  Errors: {errors}"
        ))
        if created > 0:
            self.stdout.write(self.style.SUCCESS(
                "Users can now log in with username + password. "
                "Supabase UIDs will be auto-linked in Django on first login."
            ))
