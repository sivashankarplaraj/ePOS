from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from manage_orders.models import Order, OrderLine
from update_till.models import KMeal, KPro, KRev, KWkVat, PdVatTb, PdItem, CombTb


class Command(BaseCommand):
    help = "Export daily CSVs (MP<ddmmyy>.CSV, PD<ddmmyy>.CSV, RV<ddmmyy>.CSV) based on orders and K* templates"

    def add_arguments(self, parser):
        parser.add_argument('--date', help='YYYY-MM-DD of the business day to export (defaults to today)', default=None)
        parser.add_argument('--outdir', help='Directory to write CSVs into', default='.')

    def handle(self, *args, **options):
        export_date = date.fromisoformat(options['date']) if options['date'] else timezone.localdate()
        outdir = Path(options['outdir']).resolve()
        outdir.mkdir(parents=True, exist_ok=True)

        # Aggregations
        start = timezone.make_aware(timezone.datetime.combine(export_date, timezone.datetime.min.time()))
        end = timezone.make_aware(timezone.datetime.combine(export_date, timezone.datetime.max.time()))

        orders = Order.objects.filter(created_at__range=(start, end))

        # Reset working tables (optional: we simply compute on the fly; the K* models act as schemas)
        # Build dicts keyed by PRODNUMB
        meal_counts = {}  # { prod: { 'TAKEAWAY': x, 'EATIN': y } }
        kpro_counts = {}  # { (prodnum, combo): {TAKEAWAY, EATIN, WASTE, STAFF, OPTION} }

        # KRev totals
        rev = {
            'TCASHVAL': 0, 'TCHQVAL': 0, 'TCARDVAL': 0, 'TONACCOUNT': 0,
            'TSTAFFVAL': 0, 'TWASTEVAL': 0, 'TCOUPVAL': 0, 'TPAYOUTVA': 0,
            'TTOKENVAL': 0, 'TDISCNTVA': 0, 'TTOKENNOVR': 0, 'TGOLARGENU': 0,
            'TMEAL_DISCNT': 0, 'ACTCASH': 0, 'ACTCHQ': 0, 'ACTCARD': 0, 'VAT': 0, 'XPV': 0,
        }

        # Payment mapping
        pay_map = {
            'cash': 'TCASHVAL',
            'card': 'TCARDVAL',
            'cheque': 'TCHQVAL',
            'on_account': 'TONACCOUNT',
        }

        # Prepare VAT maps for KWkVat aggregation
        vat_rate_by_class = {p.VAT_CLASS: float(p.VAT_RATE) for p in PdVatTb.objects.all()}
        pd_items = {p.PRODNUMB: (p.EAT_VAT_CLASS, p.TAKE_VAT_CLASS) for p in PdItem.objects.all().only('PRODNUMB','EAT_VAT_CLASS','TAKE_VAT_CLASS')}
        combos = {c.COMBONUMB: (c.EAT_VAT_CLASS, c.TAKE_VAT_CLASS) for c in CombTb.objects.all().only('COMBONUMB','EAT_VAT_CLASS','TAKE_VAT_CLASS')}
        # per VAT class totals for this day
        vat_due_by_class = {}      # pennies VAT per class
        excl_val_by_class = {}     # pennies net per class

        # Aggregate
        for o in orders:
            pay_key = pay_map.get(o.payment_method.lower())
            if pay_key:
                rev[pay_key] += o.total_gross or 0
            # We do not set ACT* figures here without cashup info; keep zero unless separately provided

            for line in o.lines.all():
                basis = 'TAKEAWAY' if o.vat_basis == 'take' else 'EATIN'
                key = (line.item_code, line.item_type == 'combo')
                if key not in kpro_counts:
                    kpro_counts[key] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                kpro_counts[key][basis] += line.qty
                if line.is_meal:
                    m = meal_counts.setdefault(line.item_code, {'TAKEAWAY': 0, 'EATIN': 0})
                    m[basis] += line.qty
                # Track options: if meta contains chosen_option_code for a product
                if line.item_type == 'product':
                    opt = (line.meta or {}).get('option_code')
                    if opt:
                        key_opt = (int(opt), False)
                        if key_opt not in kpro_counts:
                            kpro_counts[key_opt] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                        kpro_counts[key_opt]['OPTION'] += line.qty

                # VAT class determination for KWkVat
                vat_class = None
                if line.item_type == 'product':
                    eat_cls, take_cls = pd_items.get(line.item_code, (None, None))
                else:  # combo
                    eat_cls, take_cls = combos.get(line.item_code, (None, None))
                vat_class = take_cls if basis == 'TAKEAWAY' else eat_cls
                rate = vat_rate_by_class.get(vat_class)
                if rate is not None and line.line_total_gross:
                    g = int(line.line_total_gross)  # pence, VAT-inclusive
                    # VAT = gross - net, net = gross * 100/(100+rate)
                    net = round(g * 100.0 / (100.0 + rate))
                    vat_amt = g - net
                    vat_due_by_class[vat_class] = vat_due_by_class.get(vat_class, 0) + vat_amt
                    excl_val_by_class[vat_class] = excl_val_by_class.get(vat_class, 0) + net

        # Update KWkVat for this day (per class)
        weekday = export_date.isoweekday()  # 1..7 Monday..Sunday
        for vat_class, rate in vat_rate_by_class.items():
            # upsert row for class
            obj, _ = KWkVat.objects.get_or_create(VAT_CLASS=vat_class, defaults={
                'VAT_RATE': rate,
                **{f'TOT_VAT_{i}': 0.0 for i in range(1,8)},
                **{f'T_VAL_EXCLVAT_{i}': 0.0 for i in range(1,8)},
            })
            # keep VAT_RATE in sync
            if obj.VAT_RATE != rate:
                obj.VAT_RATE = rate
            # set today's columns (values in pounds per spec)
            vat_pounds = (vat_due_by_class.get(vat_class, 0) or 0) / 100.0
            net_pounds = (excl_val_by_class.get(vat_class, 0) or 0) / 100.0
            setattr(obj, f'TOT_VAT_{weekday}', float(vat_pounds))
            setattr(obj, f'T_VAL_EXCLVAT_{weekday}', float(net_pounds))
            obj.save(update_fields=['VAT_RATE', f'TOT_VAT_{weekday}', f'T_VAL_EXCLVAT_{weekday}', 'last_updated'])

        # Write MP<ddmmyy>.CSV from KMeal schema
        mp_name = f"MP{export_date:%d%m%y}.CSV"
        pd_name = f"PD{export_date:%d%m%y}.CSV"
        rv_name = f"RV{export_date:%d%m%y}.CSV"

        with open(outdir / mp_name, 'w', newline='', encoding='utf-8') as f:
            f.write('PRODNUMB,TAKEAWAY,EATIN\n')
            for prod, d in sorted(meal_counts.items()):
                f.write(f"{prod},{d['TAKEAWAY']},{d['EATIN']}\n")

        with open(outdir / pd_name, 'w', newline='', encoding='utf-8') as f:
            f.write('PRODNUMB,COMBO,TAKEAWAY,EATIN,WASTE,STAFF,OPTION\n')
            for (prod, combo), d in sorted(kpro_counts.items()):
                f.write(f"{prod},{1 if combo else 0},{d['TAKEAWAY']},{d['EATIN']},{d['WASTE']},{d['STAFF']},{d['OPTION']}\n")

        with open(outdir / rv_name, 'w', newline='', encoding='utf-8') as f:
            f.write('TCASHVAL,TCHQVAL,TCARDVAL,TONACCOUNT,TSTAFFVAL,TWASTEVAL,TCOUPVAL,TPAYOUTVA,TTOKENVAL,TDISCNTVA,TTOKENNOVR,TGOLARGENU,TMEAL_DISCNT,ACTCASH,ACTCHQ,ACTCARD,VAT,XPV\n')
            f.write(','.join(str(rev[k]) for k in ['TCASHVAL','TCHQVAL','TCARDVAL','TONACCOUNT','TSTAFFVAL','TWASTEVAL','TCOUPVAL','TPAYOUTVA','TTOKENVAL','TDISCNTVA','TTOKENNOVR','TGOLARGENU','TMEAL_DISCNT','ACTCASH','ACTCHQ','ACTCARD','VAT','XPV']))
            f.write('\n')

        self.stdout.write(self.style.SUCCESS(f"Exported {mp_name}, {pd_name}, {rv_name} to {outdir}"))
