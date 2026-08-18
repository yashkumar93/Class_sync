"""
Management command: evaluate_early_warning

Run nightly to flag students whose attendance + submission pattern
crosses the risk threshold configured in SystemConfig.

    py manage.py evaluate_early_warning
"""
import logging
from django.core.management.base import BaseCommand
from notifications.services import evaluate_risk_flags

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Evaluate early-warning risk flags for all active students."

    def handle(self, *args, **options):
        flagged, resolved = evaluate_risk_flags()
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {flagged} new flag(s) raised, {resolved} flag(s) resolved."
            )
        )

