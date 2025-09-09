from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Tuple

from django.db import transaction
from django.utils import timezone

from manage_orders.models import Order
from update_till.models import KMeal, KPro, KRev, KWkVat, PdVatTb, PdItem, CombTb


@dataclass
class DailyStats:
    export_date: date
    meal_counts: Dict[int, Dict[str, int]]
    kpro_counts: Dict[Tuple[int, bool], Dict[str, int]]
    rev: Dict[str, int]


def _aggregate_orders(export_date: date) -> DailyStats:
    start = timezone.make_aware(timezone.datetime.combine(export_date, timezone.datetime.min.time()))
    end = timezone.make_aware(timezone.datetime.combine(export_date, timezone.datetime.max.time()))

    orders = Order.objects.filter(created_at__range=(start, end))

    meal_counts: Dict[int, Dict[str, int]] = {}
    kpro_counts: Dict[Tuple[int, bool], Dict[str, int]] = {}
    rev = {
        'TCASHVAL': 0, 'TCHQVAL': 0, 'TCARDVAL': 0, 'TONACCOUNT': 0,
        'TSTAFFVAL': 0, 'TWASTEVAL': 0, 'TCOUPVAL': 0, 'TPAYOUTVA': 0,
        'TTOKENVAL': 0, 'TDISCNTVA': 0, 'TTOKENNOVR': 0, 'TGOLARGENU': 0,
        'TMEAL_DISCNT': 0, 'ACTCASH': 0, 'ACTCHQ': 0, 'ACTCARD': 0, 'VAT': 0, 'XPV': 0,
    }

    pay_map = {
        'cash': 'TCASHVAL',
        'card': 'TCARDVAL',
        'cheque': 'TCHQVAL',
        'on_account': 'TONACCOUNT',
    }

    for o in orders:
        pay_key = pay_map.get((o.payment_method or '').lower())
        if pay_key:
            rev[pay_key] += o.total_gross or 0
        for line in o.lines.all():
            basis = 'TAKEAWAY' if o.vat_basis == 'take' else 'EATIN'
            key = (line.item_code, line.item_type == 'combo')
            if key not in kpro_counts:
                kpro_counts[key] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
            kpro_counts[key][basis] += line.qty
            if line.is_meal:
                m = meal_counts.setdefault(line.item_code, {'TAKEAWAY': 0, 'EATIN': 0})
                m[basis] += line.qty
            if line.item_type == 'product':
                opt = (line.meta or {}).get('option_code')
                if opt:
                    key_opt = (int(opt), False)
                    if key_opt not in kpro_counts:
                        kpro_counts[key_opt] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                    kpro_counts[key_opt]['OPTION'] += line.qty

    return DailyStats(export_date, meal_counts, kpro_counts, rev)


@transaction.atomic
def build_daily_stats(export_date: date) -> DailyStats:
    stats = _aggregate_orders(export_date)

    # Upsert KMeal
    for prod, d in stats.meal_counts.items():
        obj, created = KMeal.objects.select_for_update().get_or_create(
            stat_date=stats.export_date, PRODNUMB=prod,
            defaults={'TAKEAWAY': 0, 'EATIN': 0},
        )
        obj.TAKEAWAY = d['TAKEAWAY']
        obj.EATIN = d['EATIN']
        obj.save(update_fields=['TAKEAWAY', 'EATIN', 'last_updated'])

    # Upsert KPro
    for (prod, combo), d in stats.kpro_counts.items():
        obj, created = KPro.objects.select_for_update().get_or_create(
            stat_date=stats.export_date, PRODNUMB=prod, COMBO=combo,
            defaults={'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0},
        )
        obj.TAKEAWAY = d['TAKEAWAY']
        obj.EATIN = d['EATIN']
        obj.WASTE = d['WASTE']
        obj.STAFF = d['STAFF']
        obj.OPTION = d['OPTION']
        obj.save(update_fields=['TAKEAWAY', 'EATIN', 'WASTE', 'STAFF', 'OPTION', 'last_updated'])

    # Upsert KRev (single row for date)
    rev = stats.rev
    obj, created = KRev.objects.select_for_update().get_or_create(
        stat_date=stats.export_date,
        defaults={k: 0 for k in ['TCASHVAL','TCHQVAL','TCARDVAL','TONACCOUNT','TSTAFFVAL','TWASTEVAL','TCOUPVAL','TPAYOUTVA','TTOKENVAL','TDISCNTVA','TTOKENNOVR','TGOLARGENU','TMEAL_DISCNT','ACTCASH','ACTCHQ','ACTCARD','VAT','XPV']},
    )
    for k, v in rev.items():
        setattr(obj, k, v)
    obj.save(update_fields=list(rev.keys()) + ['last_updated'])

    # Update KWkVat for this date based on current PdVatTb, PdItem, CombTb and the day's orders
    vat_rate_by_class = {p.VAT_CLASS: float(p.VAT_RATE) for p in PdVatTb.objects.all()}
    pd_items = {p.PRODNUMB: (p.EAT_VAT_CLASS, p.TAKE_VAT_CLASS) for p in PdItem.objects.all().only('PRODNUMB','EAT_VAT_CLASS','TAKE_VAT_CLASS')}
    combos = {c.COMBONUMB: (c.EAT_VAT_CLASS, c.TAKE_VAT_CLASS) for c in CombTb.objects.all().only('COMBONUMB','EAT_VAT_CLASS','TAKE_VAT_CLASS')}

    # Re-aggregate VAT split quickly using the same order scan
    start = timezone.make_aware(timezone.datetime.combine(export_date, timezone.datetime.min.time()))
    end = timezone.make_aware(timezone.datetime.combine(export_date, timezone.datetime.max.time()))
    orders = Order.objects.filter(created_at__range=(start, end))
    vat_due_by_class = {}
    excl_val_by_class = {}
    for o in orders:
        for line in o.lines.all():
            basis = 'TAKEAWAY' if o.vat_basis == 'take' else 'EATIN'
            if line.item_type == 'product':
                eat_cls, take_cls = pd_items.get(line.item_code, (None, None))
            else:
                eat_cls, take_cls = combos.get(line.item_code, (None, None))
            vat_class = take_cls if basis == 'TAKEAWAY' else eat_cls
            rate = vat_rate_by_class.get(vat_class)
            if rate is not None and line.line_total_gross:
                g = int(line.line_total_gross)
                net = round(g * 100.0 / (100.0 + rate))
                vat_amt = g - net
                vat_due_by_class[vat_class] = vat_due_by_class.get(vat_class, 0) + vat_amt
                excl_val_by_class[vat_class] = excl_val_by_class.get(vat_class, 0) + net

    weekday = export_date.isoweekday()  # 1..7
    for vat_class, rate in vat_rate_by_class.items():
        kw, _ = KWkVat.objects.select_for_update().get_or_create(
            VAT_CLASS=vat_class,
            defaults={'VAT_RATE': rate, **{f'TOT_VAT_{i}': 0.0 for i in range(1,8)}, **{f'T_VAL_EXCLVAT_{i}': 0.0 for i in range(1,8)}},
        )
        if kw.VAT_RATE != rate:
            kw.VAT_RATE = rate
        vat_pounds = (vat_due_by_class.get(vat_class, 0) or 0) / 100.0
        net_pounds = (excl_val_by_class.get(vat_class, 0) or 0) / 100.0
        setattr(kw, f'TOT_VAT_{weekday}', float(vat_pounds))
        setattr(kw, f'T_VAL_EXCLVAT_{weekday}', float(net_pounds))
        kw.save(update_fields=['VAT_RATE', f'TOT_VAT_{weekday}', f'T_VAL_EXCLVAT_{weekday}', 'last_updated'])

    return stats
