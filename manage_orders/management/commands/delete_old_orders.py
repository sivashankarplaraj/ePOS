from django.core.management.base import BaseCommand
from manage_orders.models import Order
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Delete orders older than 30 days'

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted, _ = Order.objects.filter(created_at__lt=cutoff_date).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} old orders.'))

