"""
Management command: check_confirmation_timeouts

Run this on a schedule (e.g. every minute via cron or Windows Task Scheduler)
to fall through expired substitute confirmation windows.

    py manage.py check_confirmation_timeouts
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from absence.models import AbsenceReport
from absence.engine import decline_or_timeout

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process expired substitute confirmation windows and fall through to next candidate or self-study."

    def handle(self, *args, **options):
        now = timezone.now()
        expired = AbsenceReport.objects.filter(
            status=AbsenceReport.STATUS_PENDING_CONFIRMATION,
            confirmation_deadline__lt=now,
        ).select_related("proposed_substitute", "timetable_slot__section__course")

        count = expired.count()
        if count == 0:
            self.stdout.write("No expired confirmations.")
            return

        self.stdout.write(f"Processing {count} expired confirmation(s)...")
        for report in expired:
            logger.info("Confirmation timeout for AbsenceReport pk=%s", report.pk)
            self.stdout.write(
                f"  ↳ Report {report.pk}: {report.faculty.get_full_name()} — "
                f"proposed sub {report.proposed_substitute} timed out."
            )
            decline_or_timeout(report)

        self.stdout.write(self.style.SUCCESS(f"Done. Processed {count} timeouts."))
