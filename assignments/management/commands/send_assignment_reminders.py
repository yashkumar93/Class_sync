"""
Management command: send_assignment_reminders

Run every ~10 minutes via cron to fire deadline reminder notifications.
Uses ReminderLog for deduplication — safe to run repeatedly.

    py manage.py send_assignment_reminders
"""
from django.core.management.base import BaseCommand
from assignments.services import send_assignment_reminders


class Command(BaseCommand):
    help = "Send deadline reminder notifications for upcoming assignments (idempotent via ReminderLog)."

    def handle(self, *args, **options):
        sent = send_assignment_reminders()
        self.stdout.write(
            self.style.SUCCESS(f"Sent {sent} reminder notification(s).")
        )
