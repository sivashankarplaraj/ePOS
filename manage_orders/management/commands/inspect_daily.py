from datetime import date
from django.core.management.base import BaseCommand
from django.utils import timezone

from update_till.models import KRev, KPro


class Command(BaseCommand):
    help = "Inspect daily aggregated stats: prints KRev row and selected KPro rows for a date"

    def add_arguments(self, parser):
        parser.add_argument('--date', help='YYYY-MM-DD of the business day to inspect (defaults to today)', default=None)
        parser.add_argument('--codes', nargs='*', type=int, help='Optional product codes to include from KPro (non-combo rows)', default=[])

    def handle(self, *args, **options):
        target_date = date.fromisoformat(options['date']) if options['date'] else timezone.localdate()
        krev = KRev.objects.filter(stat_date=target_date).values().first()
        if not krev:
            self.stdout.write(self.style.WARNING(f"No KRev row for {target_date}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"KRev[{target_date}]: "
                f"TCASHVAL={krev['TCASHVAL']} TCHQVAL={krev['TCHQVAL']} TCARDVAL={krev['TCARDVAL']} "
                f"TONACCOUNT={krev['TONACCOUNT']} TSTAFFVAL={krev['TSTAFFVAL']} TWASTEVAL={krev['TWASTEVAL']} VAT={krev['VAT']} TDISCNTVA={krev['TDISCNTVA']}"))

        codes = options['codes']
        if codes:
            rows = list(KPro.objects.filter(stat_date=target_date, COMBO=False, PRODNUMB__in=codes).order_by('PRODNUMB').values())
            if rows:
                self.stdout.write("KPro (non-combo):")
                for r in rows:
                    self.stdout.write(f"  #{r['PRODNUMB']}: TAKEAWAY={r['TAKEAWAY']} EATIN={r['EATIN']} STAFF={r['STAFF']} WASTE={r['WASTE']} OPTION={r['OPTION']}")
            else:
                self.stdout.write("No KPro rows for provided codes.")
