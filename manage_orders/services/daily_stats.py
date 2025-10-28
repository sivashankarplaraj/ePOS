from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Tuple, List, Optional

from django.db import transaction
from django.utils import timezone

from manage_orders.models import Order
from update_till.models import KMeal, KPro, KRev, KWkVat, PdVatTb, PdItem, CombTb, CompPro, OptPro


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
    # Helpers for meal VAT expansion
    pditem_cache: Dict[int, PdItem] = {}
    def _get_pditem(code: int) -> Optional[PdItem]:
        if code in pditem_cache:
            return pditem_cache[code]
        obj = PdItem.objects.filter(PRODNUMB=code).only(
            'PRODNUMB', 'EAT_VAT_CLASS', 'TAKE_VAT_CLASS',
            'VATPR', 'DC_VATPR', 'VATPR_2', 'DC_VATPR_2', 'VATPR_3', 'DC_VATPR_3',
            'VATPR_4', 'DC_VATPR_4', 'VATPR_5', 'DC_VATPR_5', 'VATPR_6', 'DC_VATPR_6'
        ).first()
        if obj:
            pditem_cache[code] = obj
        return obj

    def _meal_effective_component_price(band: int, code: int) -> int:
        it = _get_pditem(code)
        if not it:
            return 0
        std_name = 'VATPR' if band == 1 else f'VATPR_{band}'
        dc_name = 'DC_VATPR' if band == 1 else f'DC_VATPR_{band}'
        std_val = getattr(it, std_name, 0) or 0
        dc_val = getattr(it, dc_name, 0) or 0
        return dc_val if dc_val and dc_val > 0 else std_val

    meal_counts: Dict[int, Dict[str, int]] = {}
    kpro_counts: Dict[Tuple[int, bool], Dict[str, int]] = {}
    rev = {
        'TCASHVAL': 0, 'TCHQVAL': 0, 'TCARDVAL': 0, 'TONACCOUNT': 0,
        'TSTAFFVAL': 0, 'TWASTEVAL': 0, 'TCOUPVAL': 0, 'TPAYOUTVA': 0,
        'TTOKENVAL': 0, 'TDISCNTVA': 0, 'TTOKENNOVR': 0, 'TGOLARGENU': 0,
        'TMEAL_DISCNT': 0, 'ACTCASH': 0, 'ACTCHQ': 0, 'ACTCARD': 0, 'VAT': 0, 'XPV': 0,
    }

    # Map UI payment method labels (from app_prod_order checkout buttons) to revenue accumulator fields.
    # Front-end sends the literal button text (e.g. "On Account", "Crew Food", "Waste food").
    # We normalise to lowercase and allow either spaces or underscores when mapping.
    pay_map = {
        'cash': 'TCASHVAL',            # Cash sales
        'card': 'TCARDVAL',            # Card sales
        'cheque': 'TCHQVAL',           # (Not currently exposed in UI, retained for completeness)
        'on account': 'TONACCOUNT',    # UI button: On Account
        'on_account': 'TONACCOUNT',    # underscore variant (defensive)
        'voucher': 'TCOUPVAL',         # UI button: Voucher (treated as coupon value)
        'paid out': 'TPAYOUTVA',       # UI button: Paid Out
        'paid_out': 'TPAYOUTVA',
        'crew food': 'TSTAFFVAL',      # UI button: Crew Food (staff meals)
        'crew_food': 'TSTAFFVAL',
        'waste food': 'TWASTEVAL',     # UI button: Waste food
        'waste_food': 'TWASTEVAL',
        # Additional potential future mappings could include tokens or discounts if UI adds them:
        # 'token': 'TTOKENVAL', 'discount': 'TDISCNTVA'
    }

    # Preload product price columns needed for meal discount computation.
    # We only need standard and discounted price in the active order's price band, but price band varies per order.
    # Strategy: when computing a meal discount, dynamically fetch required product records (burger, fries, drink) once and cache.
    pditem_cache: Dict[int, PdItem] = {}
    comb_cache: Dict[int, CombTb] = {}

    def _get_pditem(code: int) -> Optional[PdItem]:
        if code in pditem_cache:
            return pditem_cache[code]
        obj = PdItem.objects.filter(PRODNUMB=code).first()
        if obj:
            pditem_cache[code] = obj
        return obj

    def _meal_component_prices(band: int, burger_code: int, fries_code: int, drink_code: int) -> tuple[int,int,int,int,int]:
        """Return (burger_std, burger_meal, fries_std, fries_meal, drink_std, drink_meal) in pence for given price band.

        Falls back meal price component to standard if discounted component (DC_*) is zero.
        """
        # Column name helpers (reuse logic from views without importing to avoid circulars)
        def std_col(n: int) -> str:
            return 'VATPR' if n == 1 else f'VATPR_{n}'
        def dc_col(n: int) -> str:
            return 'DC_VATPR' if n == 1 else f'DC_VATPR_{n}'
        std = std_col(band)
        dc = dc_col(band)
        def comp(code: int) -> tuple[int,int]:
            it = _get_pditem(code)
            if not it:
                return 0,0
            std_val = getattr(it, std, 0) or 0
            dc_val = getattr(it, dc, 0) or 0
            eff_meal = dc_val if dc_val and dc_val > 0 else std_val
            return std_val, eff_meal
        b_std, b_meal = comp(burger_code)
        f_std, f_meal = comp(fries_code)
        d_std, d_meal = comp(drink_code)
        return b_std, b_meal, f_std, f_meal, d_std, d_meal

    # Preload combination component mappings (compulsory / optional) for combination discount computation.
    comp_pro_map: Dict[int, List[int]] = {}
    opt_pro_map: Dict[int, List[int]] = {}
    for cp in CompPro.objects.all().only('COMBONUMB','PRODNUMB'):
        comp_pro_map.setdefault(cp.COMBONUMB, []).append(cp.PRODNUMB)
    for op in OptPro.objects.all().only('COMBONUMB','PRODNUMB'):
        opt_pro_map.setdefault(op.COMBONUMB, []).append(op.PRODNUMB)

    def _combo_component_codes(combo_code: int) -> tuple[List[int], List[int]]:
        return comp_pro_map.get(combo_code, []), opt_pro_map.get(combo_code, [])

    # Small cache to avoid repeated PdItem hits during VAT pass
    pditem_cache: Dict[int, PdItem] = {}
    def _get_pditem(code: int) -> Optional[PdItem]:
        if code in pditem_cache:
            return pditem_cache[code]
        obj = PdItem.objects.filter(PRODNUMB=code).only(
            'PRODNUMB', 'EAT_VAT_CLASS', 'TAKE_VAT_CLASS',
            'VATPR', 'DC_VATPR', 'VATPR_2', 'DC_VATPR_2', 'VATPR_3', 'DC_VATPR_3',
            'VATPR_4', 'DC_VATPR_4', 'VATPR_5', 'DC_VATPR_5', 'VATPR_6', 'DC_VATPR_6'
        ).first()
        if obj:
            pditem_cache[code] = obj
        return obj

    def _meal_effective_component_price(band: int, code: int) -> int:
        """Return the effective MEAL price (discounted if available) for product code in given price band (pence)."""
        it = _get_pditem(code)
        if not it:
            return 0
        std_name = 'VATPR' if band == 1 else f'VATPR_{band}'
        dc_name = 'DC_VATPR' if band == 1 else f'DC_VATPR_{band}'
        std_val = getattr(it, std_name, 0) or 0
        dc_val = getattr(it, dc_name, 0) or 0
        return dc_val if dc_val and dc_val > 0 else std_val

    for o in orders:
        raw_method = (o.payment_method or '').strip().lower()
        # Normalise multiple internal whitespace to single space for robust matching
        norm_method = ' '.join(raw_method.split())
        pay_key = pay_map.get(norm_method) or pay_map.get(norm_method.replace(' ', '_'))
        if pay_key:
            rev[pay_key] += o.total_gross or 0
        is_staff_order = norm_method in {'crew food','crew_food'}
        is_waste_order = norm_method in {'waste food','waste_food'}

        for line in o.lines.all():
            basis = 'TAKEAWAY' if o.vat_basis == 'take' else 'EATIN'
            key = (line.item_code, line.item_type == 'combo')
            if key not in kpro_counts:
                kpro_counts[key] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
            kpro_counts[key][basis] += line.qty
            if is_staff_order:
                kpro_counts[key]['STAFF'] += line.qty
            if is_waste_order:
                kpro_counts[key]['WASTE'] += line.qty
            if line.is_meal:
                m = meal_counts.setdefault(line.item_code, {'TAKEAWAY': 0, 'EATIN': 0})
                m[basis] += line.qty
                # Meal discount accumulation (TMEAL_DISCNT): (Sum singles standard) - (Sum meal components) * qty
                meta = line.meta or {}
                burger_code = line.item_code
                fries_code = meta.get('fries') or 0
                drink_code = meta.get('drink') or 0
                try:
                    fries_code = int(fries_code) if fries_code else 0
                    drink_code = int(drink_code) if drink_code else 0
                except Exception:
                    fries_code = 0; drink_code = 0
                if fries_code and drink_code:
                    b_std, b_meal, f_std, f_meal, d_std, d_meal = _meal_component_prices(o.price_band, burger_code, fries_code, drink_code)
                    singles_total = b_std + f_std + d_std
                    meal_total = b_meal + f_meal + d_meal
                    discount = singles_total - meal_total
                    if discount > 0:
                        rev['TMEAL_DISCNT'] += discount * line.qty
                # Go Large count (TGOLARGENU): meta.go_large flag set by frontend when applied
                if (line.meta or {}).get('go_large'):
                    rev['TGOLARGENU'] += line.qty
                # PD file requirement: fries & drink components of a meal must each increment their own product's TAKEAWAY/EATIN counts (COMBO = False)
                # MP file should still only count the burger (already handled via meal_counts above) per spec.
                for comp_code in (fries_code, drink_code):
                    if comp_code:
                        key_comp = (comp_code, False)
                        if key_comp not in kpro_counts:
                            kpro_counts[key_comp] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                        kpro_counts[key_comp][basis] += line.qty
                        if is_staff_order:
                            kpro_counts[key_comp]['STAFF'] += line.qty
                        if is_waste_order:
                            kpro_counts[key_comp]['WASTE'] += line.qty
            if line.item_type == 'product':
                meta = line.meta or {}
                # Legacy single option_code handling
                opt = meta.get('option_code')
                if opt:
                    try:
                        opt_int = int(opt)
                        key_opt = (opt_int, False)
                        if key_opt not in kpro_counts:
                            kpro_counts[key_opt] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                        kpro_counts[key_opt]['OPTION'] += line.qty
                    except Exception:
                        pass
                # Multiple optional products (OPTIONAL_PROD spec): increment OPTION count for each optional product chosen.
                # Definition: OPTION is total number of this product chosen as optional product for products on the date.
                opt_list: List[int] = []
                raw_opts = meta.get('options') or []
                if isinstance(raw_opts, list):
                    for oc in raw_opts:
                        try:
                            opt_list.append(int(oc))
                        except Exception:
                            continue
                for oc in opt_list:
                    key_opt2 = (oc, False)
                    if key_opt2 not in kpro_counts:
                        kpro_counts[key_opt2] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                    kpro_counts[key_opt2]['OPTION'] += line.qty  # count appearances
                # Free choices (free_choices list) should also contribute to OPTION counts per spec (chosen as free item for a product)
                free_list: List[int] = []
                raw_free = meta.get('free_choices') or []
                if isinstance(raw_free, list):
                    for fc in raw_free:
                        try:
                            free_list.append(int(fc))
                        except Exception:
                            continue
                for fc in free_list:
                    key_free = (fc, False)
                    if key_free not in kpro_counts:
                        kpro_counts[key_free] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                    kpro_counts[key_free]['OPTION'] += line.qty
            elif line.item_type == 'combo':
                # Combination discount (TDISCNTVA): (Sum compulsory standard prices + sum selected optional prices considered free) - combo price.
                # Spec: A = amount due for all compulsory + chosen optional products; B = amount due for combo product; discount = A - B.
                # NOTE: Free allowance (e.g., first N options free) not yet parameterized; we treat ALL selected options as included in A.
                meta = line.meta or {}
                selected_opts = []
                raw_opts = meta.get('options') or []
                if isinstance(raw_opts, list):
                    for oc in raw_opts:
                        try:
                            selected_opts.append(int(oc))
                        except Exception:
                            continue
                # Increment OPTION counts for selected optional products within the combo as they are chosen as optional items.
                for oc in selected_opts:
                    key_opt_combo = (oc, False)
                    if key_opt_combo not in kpro_counts:
                        kpro_counts[key_opt_combo] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                    kpro_counts[key_opt_combo]['OPTION'] += line.qty
                # Free choices in combo context
                meta = line.meta or {}
                free_list_combo: List[int] = []
                raw_free_combo = meta.get('free_choices') or []
                if isinstance(raw_free_combo, list):
                    for fc in raw_free_combo:
                        try:
                            free_list_combo.append(int(fc))
                        except Exception:
                            continue
                for fc in free_list_combo:
                    key_free_combo = (fc, False)
                    if key_free_combo not in kpro_counts:
                        kpro_counts[key_free_combo] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                    kpro_counts[key_free_combo]['OPTION'] += line.qty
                compulsory, possible_optional = _combo_component_codes(line.item_code)
                comp_codes = compulsory[:]  # copy
                # Only include selected optional codes that are defined as optional for this combo
                for oc in selected_opts:
                    if oc in possible_optional:
                        comp_codes.append(oc)
                # PD file requirement: compulsory and selected optional component products must increment their own TAKEAWAY/EATIN counts (COMBO = False)
                if comp_codes:
                    for comp_code in comp_codes:
                        key_comp = (comp_code, False)
                        if key_comp not in kpro_counts:
                            kpro_counts[key_comp] = {'TAKEAWAY': 0, 'EATIN': 0, 'WASTE': 0, 'STAFF': 0, 'OPTION': 0}
                        kpro_counts[key_comp][basis] += line.qty
                        if is_staff_order:
                            kpro_counts[key_comp]['STAFF'] += line.qty
                        if is_waste_order:
                            kpro_counts[key_comp]['WASTE'] += line.qty
                if comp_codes:
                    # Sum standard prices for each component in the order's price band
                    def std_col(n: int) -> str:
                        return 'VATPR' if n == 1 else f'VATPR_{n}'
                    std_name = std_col(o.price_band)
                    total_components = 0
                    for code in comp_codes:
                        item_obj = _get_pditem(code)
                        if item_obj:
                            total_components += getattr(item_obj, std_name, 0) or 0
                    combo_price = line.unit_price_gross or 0
                    discount = total_components - combo_price
                    if discount > 0:
                        rev['TDISCNTVA'] += discount * line.qty

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
    # At this point VAT, ACT* may still be zero; we'll set VAT after the VAT pass below.
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
    # Local helpers for meal VAT expansion in this VAT pass
    _pditem_vat_cache: Dict[int, PdItem] = {}
    def _vat_get_pditem(code: int) -> Optional[PdItem]:
        if code in _pditem_vat_cache:
            return _pditem_vat_cache[code]
        obj = PdItem.objects.filter(PRODNUMB=code).only(
            'PRODNUMB', 'EAT_VAT_CLASS', 'TAKE_VAT_CLASS',
            'VATPR', 'DC_VATPR', 'VATPR_2', 'DC_VATPR_2', 'VATPR_3', 'DC_VATPR_3',
            'VATPR_4', 'DC_VATPR_4', 'VATPR_5', 'DC_VATPR_5', 'VATPR_6', 'DC_VATPR_6'
        ).first()
        if obj:
            _pditem_vat_cache[code] = obj
        return obj

    def _vat_meal_effective_component_price(band: int, code: int) -> int:
        it = _vat_get_pditem(code)
        if not it:
            return 0
        std_name = 'VATPR' if band == 1 else f'VATPR_{band}'
        dc_name = 'DC_VATPR' if band == 1 else f'DC_VATPR_{band}'
        std_val = getattr(it, std_name, 0) or 0
        dc_val = getattr(it, dc_name, 0) or 0
        return dc_val if dc_val and dc_val > 0 else std_val

    vat_due_by_class: Dict[int, int] = {}
    excl_val_by_class: Dict[int, int] = {}
    total_vat_all = 0
    for o in orders:
        # Identify staff/waste orders for KWkVat exclusion; KRev VAT includes all
        raw_method = (o.payment_method or '').strip().lower()
        norm_method = ' '.join(raw_method.split())
        is_staff = norm_method in {'crew food', 'crew_food'}
        is_waste = norm_method in {'waste food', 'waste_food'}
        for line in o.lines.all():
            basis = 'TAKEAWAY' if o.vat_basis == 'take' else 'EATIN'
            # If this is a meal line, split VAT across its component products using their classes and meal component prices
            if getattr(line, 'is_meal', False):
                meta = line.meta or {}
                burger_code = line.item_code
                fries_code_raw = meta.get('fries')
                drink_code_raw = meta.get('drink')
                try:
                    fries_code = int(fries_code_raw) if fries_code_raw else 0
                except Exception:
                    fries_code = 0
                try:
                    drink_code = int(drink_code_raw) if drink_code_raw else 0
                except Exception:
                    drink_code = 0
                comp_codes: List[int] = [c for c in [burger_code, fries_code, drink_code] if c]
                if comp_codes:
                    # Compute effective meal price per component in this order's price band
                    comp_prices = {
                        burger_code: _vat_meal_effective_component_price(o.price_band, burger_code)
                    }
                    if fries_code:
                        comp_prices[fries_code] = _vat_meal_effective_component_price(o.price_band, fries_code)
                    if drink_code:
                        comp_prices[drink_code] = _vat_meal_effective_component_price(o.price_band, drink_code)
                    # For each component, compute VAT using its own class for the current basis
                    for code in comp_codes:
                        eat_cls, take_cls = pd_items.get(code, (None, None))
                        vat_class = take_cls if basis == 'TAKEAWAY' else eat_cls
                        rate = vat_rate_by_class.get(vat_class)
                        price_gross = int(comp_prices.get(code, 0)) * int(line.qty or 1)
                        if rate is None or price_gross <= 0:
                            continue
                        net = int(round(price_gross * 100.0 / (100.0 + rate))) if rate > 0 else price_gross
                        vat_amt = price_gross - net
                        if not (is_staff or is_waste):
                            vat_due_by_class[vat_class] = (vat_due_by_class.get(vat_class, 0) or 0) + vat_amt
                            excl_val_by_class[vat_class] = (excl_val_by_class.get(vat_class, 0) or 0) + net
                        total_vat_all += vat_amt
                # Done with meal expansion for this line
                continue
            # Non-meal lines: existing behavior
            if line.item_type == 'product':
                eat_cls, take_cls = pd_items.get(line.item_code, (None, None))
            else:
                eat_cls, take_cls = combos.get(line.item_code, (None, None))
            vat_class = take_cls if basis == 'TAKEAWAY' else eat_cls
            rate = vat_rate_by_class.get(vat_class)
            if rate is None or not line.line_total_gross:
                continue
            g = int(line.line_total_gross)
            net = int(round(g * 100.0 / (100.0 + rate))) if rate > 0 else g
            vat_amt = g - net
            if not (is_staff or is_waste):
                vat_due_by_class[vat_class] = (vat_due_by_class.get(vat_class, 0) or 0) + vat_amt
                excl_val_by_class[vat_class] = (excl_val_by_class.get(vat_class, 0) or 0) + net
            total_vat_all += vat_amt

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

    # After KWkVat update, compute total VAT (exclude staff & waste per spec of KWkVat, but KRev wants total VAT due overall).
    # We already computed vat_due_by_class in pence above; sum them.
    total_vat = total_vat_all
    # Refresh / update KRev VAT & ACT* if unset
    krevc = KRev.objects.select_for_update().get(stat_date=export_date)
    if krevc.VAT != total_vat:
        krevc.VAT = total_vat
    # Mirror ACTCASH/ACTCARD/ACTCHQ to transactional totals if they are zero (no manual reconciliation captured).
    if krevc.ACTCASH == 0:
        krevc.ACTCASH = krevc.TCASHVAL
    if krevc.ACTCARD == 0:
        krevc.ACTCARD = krevc.TCARDVAL
    if krevc.ACTCHQ == 0:
        krevc.ACTCHQ = krevc.TCHQVAL
    krevc.save(update_fields=['VAT','ACTCASH','ACTCARD','ACTCHQ','last_updated'])
    return stats
