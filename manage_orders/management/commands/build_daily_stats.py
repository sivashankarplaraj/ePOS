from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from manage_orders.services.daily_stats import build_daily_stats


class Command(BaseCommand):
    help = "Compute and upsert daily stats (KMeal, KPro, KRev, KWkVat) for a given date"

    def add_arguments(self, parser):
        parser.add_argument('--date', help='YYYY-MM-DD of the business day (defaults to today)', default=None)

    def handle(self, *args, **options):
        export_date = date.fromisoformat(options['date']) if options['date'] else timezone.localdate()
        stats = build_daily_stats(export_date)
        self.stdout.write(self.style.SUCCESS(f"Built daily stats for {export_date}: {len(stats.meal_counts)} meals, {len(stats.kpro_counts)} product keys"))
