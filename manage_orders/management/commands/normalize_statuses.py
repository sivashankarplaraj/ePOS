from django.core.management.base import BaseCommand
from django.db import transaction
from manage_orders.models import Order

class Command(BaseCommand):
    help = "Normalize any misspelled order statuses (e.g., 'dispached' -> 'dispatched') and report counts."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not write changes, only report.')

    def handle(self, *args, **options):
        dry = options.get('dry_run', False)
        typo = 'dispached'
        correct = 'dispatched'
        qs = Order.objects.filter(status=typo)
        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No records to normalize.'))
            return
        self.stdout.write(f"Found {count} orders with status '{typo}'.")
        if dry:
            self.stdout.write(self.style.WARNING('Dry run: no changes written.'))
            return
        with transaction.atomic():
            updated = qs.update(status=correct)
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} orders to \"{correct}\".'))
