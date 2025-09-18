from django.core.management.base import BaseCommand
from manage_orders.models import Order
from update_till.models import KMeal, KPro, KRev, KWkVat
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Delete orders/K meals/K pros/K revs/K wk vats older than 30 days'

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_orders, _ = Order.objects.filter(created_at__lt=cutoff_date).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_orders} old orders.'))
        # Note: KMeal, KPro, KRev, KWkVat entries are deleted via last updated  date
        deleted_kmeals, _ = KMeal.objects.filter(last_updated__lt=cutoff_date).delete()
        deleted_kpros, _ = KPro.objects.filter(last_updated__lt=cutoff_date).delete()
        deleted_krevs, _ = KRev.objects.filter(last_updated__lt=cutoff_date).delete()
        deleted_kwk_vats, _ = KWkVat.objects.filter(last_updated__lt=cutoff_date).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_kmeals} old KMeals.'))
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_kpros} old KPros.'))
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_krevs} old KRevs.'))
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_kwk_vats} old KWkVats.'))
