from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from manage_orders.services.daily_stats import build_daily_stats
from django.db import transaction
from update_till.models import KMeal, KPro, KRev, KWkVat


class Command(BaseCommand):
    help = "Export daily CSVs (MP<ddmmyy>.CSV, PD<ddmmyy>.CSV, RV<ddmmyy>.CSV) based on orders and K* templates"

    def add_arguments(self, parser):
        parser.add_argument('--date', help='YYYY-MM-DD of the business day to export (defaults to today)', default=None)
        parser.add_argument('--outdir', help='Directory to write CSVs into', default='.')
        parser.add_argument('--clear', action='store_true', help='After successful export, clear ALL rows in KMeal, KPro, KRev and KWkVat (use with caution).')

    def handle(self, *args, **options):
        export_date = date.fromisoformat(options['date']) if options['date'] else timezone.localdate()
        outdir = Path(options['outdir']).resolve()
        outdir.mkdir(parents=True, exist_ok=True)

        # Ensure stats are built/upserted for the day
        build_daily_stats(export_date)

        # Write MP<ddmmyy>.CSV from KMeal schema
        mp_name = f"MP{export_date:%d%m%y}.CSV"
        pd_name = f"PD{export_date:%d%m%y}.CSV"
        rv_name = f"RV{export_date:%d%m%y}.CSV"

        with open(outdir / mp_name, 'w', newline='', encoding='utf-8') as f:
            f.write('PRODNUMB,TAKEAWAY,EATIN\n')
            for row in KMeal.objects.filter(stat_date=export_date).order_by('PRODNUMB').values('PRODNUMB','TAKEAWAY','EATIN'):
                f.write(f"{row['PRODNUMB']},{row['TAKEAWAY']},{row['EATIN']}\n")

        with open(outdir / pd_name, 'w', newline='', encoding='utf-8') as f:
            f.write('PRODNUMB,COMBO,TAKEAWAY,EATIN,WASTE,STAFF,OPTION\n')
            for row in KPro.objects.filter(stat_date=export_date).order_by('PRODNUMB','COMBO').values('PRODNUMB','COMBO','TAKEAWAY','EATIN','WASTE','STAFF','OPTION'):
                f.write(f"{row['PRODNUMB']},{1 if row['COMBO'] else 0},{row['TAKEAWAY']},{row['EATIN']},{row['WASTE']},{row['STAFF']},{row['OPTION']}\n")

        with open(outdir / rv_name, 'w', newline='', encoding='utf-8') as f:
            f.write('TCASHVAL,TCHQVAL,TCARDVAL,TONACCOUNT,TSTAFFVAL,TWASTEVAL,TCOUPVAL,TPAYOUTVA,TTOKENVAL,TDISCNTVA,TTOKENNOVR,TGOLARGENU,TMEAL_DISCNT,ACTCASH,ACTCHQ,ACTCARD,VAT,XPV\n')
            row = KRev.objects.filter(stat_date=export_date).values('TCASHVAL','TCHQVAL','TCARDVAL','TONACCOUNT','TSTAFFVAL','TWASTEVAL','TCOUPVAL','TPAYOUTVA','TTOKENVAL','TDISCNTVA','TTOKENNOVR','TGOLARGENU','TMEAL_DISCNT','ACTCASH','ACTCHQ','ACTCARD','VAT','XPV').first() or {}
            keys = ['TCASHVAL','TCHQVAL','TCARDVAL','TONACCOUNT','TSTAFFVAL','TWASTEVAL','TCOUPVAL','TPAYOUTVA','TTOKENVAL','TDISCNTVA','TTOKENNOVR','TGOLARGENU','TMEAL_DISCNT','ACTCASH','ACTCHQ','ACTCARD','VAT','XPV']
            f.write(','.join(str(row.get(k, 0)) for k in keys))
            f.write('\n')

        self.stdout.write(self.style.SUCCESS(f"Built stats and exported {mp_name}, {pd_name}, {rv_name} to {outdir}"))

        if options.get('clear'):
            with transaction.atomic():
                kmeal_count = KMeal.objects.count()
                kpro_count = KPro.objects.count()
                krev_count = KRev.objects.count()
                kwkvat_count = KWkVat.objects.count()
                KMeal.objects.all().delete()
                KPro.objects.all().delete()
                KRev.objects.all().delete()
                KWkVat.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"Cleared tables: KMeal({kmeal_count}), KPro({kpro_count}), KRev({krev_count}), KWkVat({kwkvat_count})."))
