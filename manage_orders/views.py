from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from django.db import transaction
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from update_till.models import (
    PdItem, AppProd, GroupTb, PChoice, CombTb, AppComb, PdVatTb, CompPro, OptPro
)
from pathlib import Path
import json

# Load local_menu.json file and read it first
# group the list of menu category

def _price_band_map():
        """
        Price Band Map

        The numeric value (as string) assigned to each channel / scenario below is the <band>
        which selects the correct set of price columns from table PDITEM<n> (and COMBTB<n>)
        according to the data definitions provided.

        Column families (prices are stored in pence including VAT):
            Standard price columns (single product / combination product):
                VATPR       -> Band 1 ("standard price")
                VATPR_2     -> Band 2
                VATPR_3     -> Band 3
                VATPR_4     -> Band 4
                VATPR_5     -> Band 5
                VATPR_6     -> Band 6

            Discounted meal price columns (for meal products):
                DC_VATPR    -> Discounted Band 1
                DC_VATPR_2  -> Discounted Band 2
                DC_VATPR_3  -> Discounted Band 3
                DC_VATPR_4  -> Discounted Band 4
                DC_VATPR_5  -> Discounted Band 5
                DC_VATPR_6  -> Discounted Band 6

        Therefore when a price band value 'k' (1..6) is chosen at runtime:
            Standard (non‑meal) price column    = VATPR if k == 1 else f"VATPR_{k}"
            Meal discounted price column        = DC_VATPR if k == 1 else f"DC_VATPR_{k}"

        The mapping below associates each order source / fulfilment type with the
        appropriate price band number (as per business rules). These labels combine:
            - Channel (e.g. 'Sams online', 'Just Eat', 'Phone Order', 'Deliveroo', etc.)
            - (Optional) Branch indicator like (B) or (C)
            - Fulfilment mode: Deliver / Collect
            - A short suffix (SO, JE, DV, etc.) and a final -D or -C for Deliver/Collect

        Modify the numeric band values if business pricing rules change; the column name
        derivation above will remain valid.
        """
        return {
        'Standard-OT-C': '1',
        'Standard (B)-OB-C': '5',
        'Sams online - Deliver-SO-D': '4',
        'Sams online (B) - Deliver-SB-D': '4',
        'Sams online (C) - Deliver-SC-D': '4',
        'Just Eat - Deliver-JE-D': '6',
        'UBER - Deliver-UB-D': '6',
        'Deliveroo - Deliver-DV-D': '3',
        'Deliveroo (B) - Deliver-DB-D': '6',
        'YoYo - Deliver-YY-D': '4',
        'YoYo (B) - Deliver-YB-D': '4',
        'Phone Order - Deliver-PO-D': '2',
        'Phone Order (B) - Deliver-PB-D': '4',
        'Phone Order (C) - Deliver-PC-D': '2',
        'Phone Order - Collect-PO-C': '2',
        'Phone Order (C) - Collect-PC-C': '2',
        'YoYo - Collect-YY-C': '2',
        'UBER - Collect-UB-C': '6',
        'Deliveroo - Collect-DV-C': '3',
        'Deliveroo (B) - Collect-DB-C': '6',
        'Just Eat - Collect-JE-C': '6',
        'Sams online - Collect-SO-C': '2'
    }

@ensure_csrf_cookie
def index(request):
    # Landing page could become a dashboard; for now redirect logic optional
    return order(request)

@ensure_csrf_cookie
def order(request):
    context = {
        'price_band': _price_band_map(),
    }
    return render(request, 'manage_orders/order.html', context)


@ensure_csrf_cookie
def dashboard(request):
    return render(request, 'manage_orders/dashboard.html')

@ensure_csrf_cookie
def app_prod_order(request):
    # GroupTb is the menu category
    context = {
        # 'price_band': _price_band_map(),
        'menu_categories': GroupTb.objects.all()
    }
    return render(request, 'manage_orders/app_prod_order.html', context)

def _price_column_name(band: str, discounted: bool) -> str:
    """Return model field name for given band and discounted flag.

    band is a string '1'..'6' as produced by _price_band_map values.
    """
    base = 'DC_VATPR' if discounted else 'VATPR'
    return base if str(band) == '1' else f"{base}_{band}"


def _vat_rate_map():
    return {r.VAT_CLASS: r.VAT_RATE for r in PdVatTb.objects.all()}


def _serialize_product(item: PdItem, band: str, app_meta: AppProd | None = None, vat_rates: dict | None = None) -> dict:
    """Serialize a PdItem to JSON including standard & discounted price for chosen band.

    app_meta: corresponding AppProd row (for grouping / meal flags / variants) if available
    """
    std_col = _price_column_name(band, discounted=False)
    dc_col = _price_column_name(band, discounted=True)
    std_price = getattr(item, std_col, None)
    dc_price = getattr(item, dc_col, None)
    std_price = int(std_price) if std_price is not None else 0
    dc_price = int(dc_price) if dc_price is not None else 0
    vat_rates = vat_rates or {}
    take_vat = vat_rates.get(getattr(item, 'TAKE_VAT_CLASS', None), 0.0)
    eat_vat = vat_rates.get(getattr(item, 'EAT_VAT_CLASS', None), 0.0)
    def net(gross, rate):
        try:
            return int(round(gross / (1 + (rate/100.0)))) if gross else 0
        except ZeroDivisionError:
            return gross
    data = {
        'type': 'product',
        'code': item.PRODNUMB,
        'name': (item.PRODNAME or '').strip(),
        'band': band,
        'price_gross': std_price,
        'price_net_take': net(std_price, take_vat),
        'price_net_eat': net(std_price, eat_vat),
        'discounted_price_gross': dc_price,
        'discounted_price_net_take': net(dc_price, take_vat),
        'discounted_price_net_eat': net(dc_price, eat_vat),
    'T_DRINK_CD': getattr(item, 'T_DRINK_CD', 0) or 0,
        'meal_only': bool(getattr(item, 'MEAL_ONLY', False)),
        'has_discount': (dc_price and dc_price != std_price),
        'take_vat_rate': take_vat,
        'eat_vat_rate': eat_vat,
        'variants': []
    }
    # Meal flag from AppProd (MEAL_ID > 0 indicates appears in meal section)
    if app_meta:
        data['meal_flag'] = app_meta.MEAL_ID > 0
        # Double / triple variants
        variant_codes = []
        if app_meta.DOUBLE_PDNUMB and app_meta.DOUBLE_PDNUMB != 0:
            variant_codes.append(('double', app_meta.DOUBLE_PDNUMB))
        if app_meta.TRIPLE_PDNUMB and app_meta.TRIPLE_PDNUMB != 0:
            variant_codes.append(('triple', app_meta.TRIPLE_PDNUMB))
        # Look up variants only once (caller may supply pre-fetched map)
        for label, vcode in variant_codes:
            # variant product may not exist in PdItem table (skip if not)
            vitem = PdItem.objects.filter(PRODNUMB=vcode).only('PRODNUMB', std_col, dc_col).first()
            if vitem:
                v_std = getattr(vitem, std_col, 0) or 0
                v_dc = getattr(vitem, dc_col, 0) or 0
                data['variants'].append({
                    'label': label,
                    'code': vitem.PRODNUMB,
                    'price_gross': int(v_std),
                    'discounted_price_gross': int(v_dc) if v_dc else 0
                })
    else:
        data['meal_flag'] = False
    return data


def _serialize_combo(combo: CombTb, band: str, app_meta: AppComb | None = None, vat_rates: dict | None = None) -> dict:
    std_col = _price_column_name(band, discounted=False)
    std_price = getattr(combo, std_col, None)
    std_price = int(std_price) if std_price is not None else 0
    vat_rates = vat_rates or {}
    take_vat = vat_rates.get(getattr(combo, 'TAKE_VAT_CLASS', None), 0.0)
    eat_vat = vat_rates.get(getattr(combo, 'EAT_VAT_CLASS', None), 0.0)
    def net(gross, rate):
        try:
            return int(round(gross / (1 + (rate/100.0)))) if gross else 0
        except ZeroDivisionError:
            return gross
    data = {
        'type': 'combo',
        'code': combo.COMBONUMB,
        'name': (combo.DESC or '').strip(),
        'band': band,
        'price_gross': std_price,
        'price_net_take': net(std_price, take_vat),
        'price_net_eat': net(std_price, eat_vat),
        'take_vat_rate': take_vat,
        'eat_vat_rate': eat_vat,
        'variants': [],
        'meal_flag': False,
        'has_discount': False
    }
    # Trade-up combination (large)
    if combo.T_COMB_NUM and combo.T_COMB_NUM != 0:
        t_combo = CombTb.objects.filter(COMBONUMB=combo.T_COMB_NUM).only('COMBONUMB', std_col).first()
        if t_combo:
            t_price = getattr(t_combo, std_col, 0) or 0
            data['variants'].append({
                'label': 'trade_up',
                'code': t_combo.COMBONUMB,
                'price_gross': int(t_price)
            })
    return data


@require_GET
def api_menu(request: HttpRequest):
    """Return menu categories and their products for a given price band.

    Query params:
        band: required (1..6)
        include_empty: optional (1/true) to include categories with zero products
    Response structure:
    {
        "band": "1",
        "categories": [
            { "id": <int>, "name": "Burgers", "products": [ {..product..}, ... ] }, ...
        ]
    }
    """
    band = request.GET.get('band')
    if band not in {'1','2','3','4','5','6'}:
        return JsonResponse({'error': 'Invalid or missing band'}, status=400)
    include_empty = request.GET.get('include_empty', '').lower() in {'1','true','yes'}

    vat_rates = _vat_rate_map()
    # Products
    app_products = list(AppProd.objects.all())
    pd_items_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=[ap.PRODNUMB for ap in app_products])}
    products_by_group: dict[int, list] = {}
    for ap in app_products:
        pd_item = pd_items_map.get(ap.PRODNUMB)
        if not pd_item:
            continue
        products_by_group.setdefault(ap.GROUP_ID, []).append(_serialize_product(pd_item, band, app_meta=ap, vat_rates=vat_rates))

    # Combinations
    app_combos = list(AppComb.objects.all())
    comb_map = {c.COMBONUMB: c for c in CombTb.objects.filter(COMBONUMB__in=[ac.COMBONUMB for ac in app_combos])}
    combos_by_group: dict[int, list] = {}
    for ac in app_combos:
        comb = comb_map.get(ac.COMBONUMB)
        if not comb:
            continue
        combos_by_group.setdefault(ac.GROUP_ID, []).append(_serialize_combo(comb, band, app_meta=ac, vat_rates=vat_rates))

    categories = []
    for grp in GroupTb.objects.all().order_by('GROUP_ID'):
        items = []
        # SOURCE_TYPE: 'P' products, 'C' combos (but a group might conceptually hold both; merge if present)
        items.extend(products_by_group.get(grp.GROUP_ID, []))
        items.extend(combos_by_group.get(grp.GROUP_ID, []))
        if items or include_empty:
            categories.append({
                'id': grp.GROUP_ID,
                'name': (grp.GROUP_NAME or '').strip(),
                'source_type': grp.SOURCE_TYPE,
                'meal_group': grp.MEAL_GROUP,
                'items': sorted(items, key=lambda x: x['name'])
            })

    return JsonResponse({'band': band, 'categories': categories, 'vat_rates': vat_rates})


@require_GET
def api_product_options(request: HttpRequest, prod_code: int):
    """Return optional products (P_CHOICE) for a given product code.

    Query params:
        band: required (1..6) for pricing options
    Response { product: <code>, options: [ { code, name, price, discounted_price }, ... ] }
    """
    band = request.GET.get('band')
    if band not in {'1','2','3','4','5','6'}:
        return JsonResponse({'error': 'Invalid or missing band'}, status=400)

    links = PChoice.objects.filter(PRODNUMB=prod_code)
    opt_codes = [l.OPT_PRODNUMB for l in links]
    items = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=opt_codes)}
    options = [_serialize_product(items[c], band) for c in opt_codes if c in items]
    return JsonResponse({'product': prod_code, 'band': band, 'options': options})


def _variant_map_for_product(app_meta: AppProd):
    m = {}
    if app_meta.DOUBLE_PDNUMB:
        m['double'] = app_meta.DOUBLE_PDNUMB
    if app_meta.TRIPLE_PDNUMB:
        m['triple'] = app_meta.TRIPLE_PDNUMB
    return m


def _price_snapshot(item, band: str, discounted: bool = False):
    col = _price_column_name(band, discounted)
    val = getattr(item, col, None)
    return int(val) if val is not None else 0


@require_GET
def api_item_detail(request: HttpRequest, item_type: str, code: int):
    """Detailed info for an item (product or combo) including variants, options and meal components.

    item_type: 'product' | 'combo'
    Query params:
        band: required
    """
    band = request.GET.get('band')
    if band not in {'1','2','3','4','5','6'}:
        return JsonResponse({'error': 'Invalid or missing band'}, status=400)
    vat_rates = _vat_rate_map()
    detail = {}
    if item_type == 'product':
        app_meta = AppProd.objects.filter(PRODNUMB=code).first()
        item = PdItem.objects.filter(PRODNUMB=code).first()
        if not item:
            return JsonResponse({'error': 'Not found'}, status=404)
        base = _serialize_product(item, band, app_meta=app_meta, vat_rates=vat_rates)
        # Options from PChoice
        opt_links = PChoice.objects.filter(PRODNUMB=code)
        opt_codes = [o.OPT_PRODNUMB for o in opt_links]
        opt_items = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=opt_codes)}
        base['options'] = []
        for c in opt_codes:
            p = opt_items.get(c)
            if p:
                base['options'].append(_serialize_product(p, band, vat_rates=vat_rates))
        # Meal components heuristic: fries + drink when meal_flag; MEAL_DRINK marks drink group (value 1 in sample CSV) & fries recognized by name contains FRIES
        meal_components = []
        if base.get('meal_flag'):
            fries = PdItem.objects.filter(PRODNUMB__in=[30,31])
            drinks = PdItem.objects.filter(MEAL_DRINK__gt=0)
            meal_components = {
                'fries': [_serialize_product(f, band, vat_rates=vat_rates) for f in fries],
                'drinks': [_serialize_product(d, band, vat_rates=vat_rates) for d in drinks],
            }
        base['meal_components'] = meal_components
        detail = base
    elif item_type == 'combo':
        appc = AppComb.objects.filter(COMBONUMB=code).first()
        combo = CombTb.objects.filter(COMBONUMB=code).first()
        if not combo:
            return JsonResponse({'error': 'Not found'}, status=404)
        base = _serialize_combo(combo, band, app_meta=appc, vat_rates=vat_rates)
        # Compulsory & optional components
        comp_links = list(CompPro.objects.filter(COMBONUMB=code))
        opt_links = list(OptPro.objects.filter(COMBONUMB=code))
        comp_codes = [c.PRODNUMB for c in comp_links]
        opt_codes = [o.PRODNUMB for o in opt_links]
        comp_items = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=comp_codes)}
        opt_items = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=opt_codes)}
        base['compulsory'] = [_serialize_product(comp_items[c], band, vat_rates=vat_rates) for c in comp_codes if c in comp_items]
        base['optional'] = [_serialize_product(opt_items[c], band, vat_rates=vat_rates) for c in opt_codes if c in opt_items]
        # Free optional allowances heuristic: look for dips keyword or infer from documentation (hard to derive generically) -> placeholder free_opt_count=2 if 'dip' in any optional name and len(optional)>1
        dip_like = [o for o in base['optional'] if 'dip' in o['name'].lower()]
        base['free_optional_count'] = 2 if dip_like else 0
        detail = base
    else:
        return JsonResponse({'error': 'Invalid item_type'}, status=400)
    return JsonResponse({'band': band, 'item': detail})


@require_GET
def api_prices(request):
    """Return prices for given PRODNUMB list and price band.

    Query params:
      - band: required, '1'..'6'
      - prods: required, comma-separated integers
      - discounted: optional, '1'/'true' for discounted meal price; default false

    Response JSON:
      { "prices": { "<prod>": {"price": <int>, "dc_price": <int> } , ... }, "not_found": [<prod>, ...] }
    All prices are in pence (integers) as stored.
    """
    band = request.GET.get('band')
    prods_raw = request.GET.get('prods', '')
    if not band or not prods_raw:
        return JsonResponse({
            'error': 'Missing band or prods'
        }, status=400)

    # Parse products list
    try:
        prod_ids = [int(p) for p in prods_raw.split(',') if p.strip()]
    except ValueError:
        return JsonResponse({'error': 'Invalid prods list'}, status=400)

    # Resolve column names for both standard and discounted for flexibility
    std_col = _price_column_name(band, discounted=False)
    dc_col = _price_column_name(band, discounted=True)

    qs = PdItem.objects.filter(PRODNUMB__in=prod_ids).only('PRODNUMB', std_col, dc_col)

    prices = {}
    found_ids = set()
    for item in qs:
        found_ids.add(item.PRODNUMB)
        std_price = getattr(item, std_col, None)
        dc_price = getattr(item, dc_col, None)
        # Normalize None to 0
        prices[str(item.PRODNUMB)] = {
            'price': int(std_price) if std_price is not None else 0,
            'dc_price': int(dc_price) if dc_price is not None else 0,
        }

    not_found = [pid for pid in prod_ids if pid not in found_ids]
    return JsonResponse({'prices': prices, 'not_found': not_found})


@require_POST
def api_submit_order(request: HttpRequest):
    """Persist an order with lines.

    Expected JSON body:
    {
      "price_band": "1",
      "vat_basis": "take"|"eat",
      "show_net": true/false,
      "lines": [
         {"code":123, "type":"product"|"combo", "name":"Burger", "variant":"double", "meal":false, "qty":1, "price_gross":599}
      ]
    }
    Returns { order_id, total_gross }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    band = str(payload.get('price_band'))
    if band not in {'1','2','3','4','5','6'}:
        return JsonResponse({'error': 'Invalid price_band'}, status=400)
    vat_basis = payload.get('vat_basis')
    if vat_basis not in {'take','eat'}:
        return JsonResponse({'error': 'Invalid vat_basis'}, status=400)
    lines = payload.get('lines') or []
    # Optional payment details (from checkout modal)
    payment_method = (payload.get('payment_method') or 'Cash').strip()
    crew_id = str(payload.get('crew_id') or '0').strip()
    if crew_id == '':
        return JsonResponse({'error': 'Crew ID is required'}, status=400)
    if not isinstance(lines, list) or not lines:
        return JsonResponse({'error': 'No lines supplied'}, status=400)
    from .models import Order, OrderLine
    total_gross = 0
    total_net = 0
    # Helper inside view so it can access band variable
    def _compute_meal_price(burger_code: int, fries_code: int, drink_code: int, option_codes: list[int]):
        """Compute meal unit price (gross, in pence) from its components for given price band.

        Business rule (derived from MEAL_DISCOUNT docs): meal price = sum of discounted component
        prices (burger, fries, drink) where a discounted (DC_) price is defined (>0), otherwise
        fall back to the component's standard price. Additional optional products always add their
        full standard price (no meal discount applied to them).
        """
        std_col = _price_column_name(band, discounted=False)
        dc_col = _price_column_name(band, discounted=True)
        codes_needed = [c for c in [burger_code, fries_code, drink_code] if c]
        if option_codes:
            codes_needed.extend(option_codes)
        items = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=codes_needed).only('PRODNUMB', std_col, dc_col)}
        def comp_price(code):
            item = items.get(code)
            if not item:
                return 0
            std_val = getattr(item, std_col, None) or 0
            dc_val = getattr(item, dc_col, None) or 0
            return dc_val if dc_val and dc_val > 0 else std_val
        burger_price = comp_price(burger_code)
        fries_price = comp_price(fries_code)
        drink_price = comp_price(drink_code)
        # Options: always standard price (no discount)
        opt_total = 0
        if option_codes:
            for oc in option_codes:
                it = items.get(oc)
                if it:
                    opt_total += getattr(it, std_col, None) or 0
        return int(burger_price + fries_price + drink_price + opt_total)

    with transaction.atomic():
        order = Order.objects.create(
            price_band=int(band),
            vat_basis=vat_basis,
            show_net=bool(payload.get('show_net')),
            payment_method=payment_method,
            crew_id=crew_id,
        )
        for ln in lines:
            try:
                code = int(ln.get('code'))
                name = (ln.get('name') or '')[:120]
                item_type = ln.get('type') if ln.get('type') in {'product','combo'} else 'product'
                variant = (ln.get('variant') or '')[:40]
                is_meal = bool(ln.get('meal'))
                qty = int(ln.get('qty') or 1)
                unit_price_gross = int(ln.get('price_gross'))
            except Exception:
                return JsonResponse({'error': 'Invalid line structure'}, status=400)
            if qty < 1:
                qty = 1
            # Meal validation: if meal flag but missing fries/drink meta, reject or strip discount
            meta_payload = ln.get('meta') or {}
            if is_meal:
                fries = meta_payload.get('fries')
                drink = meta_payload.get('drink')
                if fries in (None, '') or drink in (None, ''):
                    return JsonResponse({'error': f'Meal line for code {code} missing fries or drink selection'}, status=400)
                # Server-side authoritative meal price computation (ignore client provided meal price)
                if is_meal:
                    fries = meta_payload.get('fries')
                    drink = meta_payload.get('drink')
                    if fries in (None, '') or drink in (None, ''):
                        return JsonResponse({'error': f'Meal line for code {code} missing fries or drink selection'}, status=400)
                    try:
                        fries_code = int(fries)
                        drink_code = int(drink)
                    except Exception:
                        return JsonResponse({'error': 'Invalid fries or drink code'}, status=400)
                    option_codes = []
                    raw_opts = meta_payload.get('options') or []
                    if isinstance(raw_opts, list):
                        for oc in raw_opts:
                            try:
                                option_codes.append(int(oc))
                            except Exception:
                                continue
                    recomputed = _compute_meal_price(code, fries_code, drink_code, option_codes)
                    unit_price_gross = recomputed  # override any client value
            line_total = unit_price_gross * qty
            total_gross += line_total
            # Determine VAT rate based on basis for net calculation
            vat_rate = 0.0
            if item_type == 'product':
                prod = PdItem.objects.filter(PRODNUMB=code).only('TAKE_VAT_CLASS','EAT_VAT_CLASS').first()
                if prod:
                    vat_class = getattr(prod, 'EAT_VAT_CLASS' if vat_basis=='eat' else 'TAKE_VAT_CLASS', None)
                    if vat_class:
                        vat_map = _vat_rate_map()
                        vat_rate = vat_map.get(vat_class, 0.0)
            else:  # combo
                comb = CombTb.objects.filter(COMBONUMB=code).only('TAKE_VAT_CLASS','EAT_VAT_CLASS').first()
                if comb:
                    vat_class = getattr(comb, 'EAT_VAT_CLASS' if vat_basis=='eat' else 'TAKE_VAT_CLASS', None)
                    if vat_class:
                        vat_map = _vat_rate_map()
                        vat_rate = vat_map.get(vat_class, 0.0)
            try:
                net_unit = int(round(unit_price_gross / (1 + (vat_rate/100.0))))
            except ZeroDivisionError:
                net_unit = unit_price_gross
            total_net += net_unit * qty
            # meta_payload already extracted above
            extra = {k: v for k, v in ln.items() if k not in {'code','type','name','variant','meal','qty','price_gross','meta'}}
            meta_combined = {**meta_payload, **extra}
            OrderLine.objects.create(
                order=order,
                item_code=code,
                item_type=item_type,
                name=name,
                variant_label=variant,
                is_meal=is_meal,
                qty=qty,
                unit_price_gross=unit_price_gross,
                line_total_gross=line_total,
                meta=meta_combined
            )
        order.total_gross = total_gross
        order.total_net = int(total_net)
        order.save(update_fields=['total_gross','total_net'])
    return JsonResponse({'order_id': order.id, 'total_gross': total_gross})


@require_GET
def api_orders_summary(request: HttpRequest):
    from .models import Order
    today = timezone.now().date()
    qs = Order.objects.filter(created_at__date=today)
    pending = qs.filter(status='pending').count()
    completed = qs.filter(status='completed').count()
    return JsonResponse({'date': str(today), 'pending': pending, 'completed': completed})


@require_GET
def api_orders_pending(request: HttpRequest):
    from .models import Order
    today = timezone.now().date()
    orders = []
    for o in Order.objects.filter(status='pending', created_at__date=today).order_by('created_at').prefetch_related('lines'):
        orders.append({
            'id': o.id,
            'created_at': o.created_at.isoformat(),
            'age_seconds': int((timezone.now()-o.created_at).total_seconds()),
            'payment_method': o.payment_method,
            'crew_id': o.crew_id,
            'total_gross': o.total_gross,
            'lines': [
                {
                    'name': l.name,
                    'qty': l.qty,
                    'variant': l.variant_label,
                    'meal': l.is_meal,
                    'meta': l.meta
                } for l in o.lines.all()
            ]
        })
    return JsonResponse({'orders': orders})


@require_POST
def api_order_complete(request: HttpRequest, order_id: int):
    from .models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error':'Not found'}, status=404)
    if order.status == 'completed':
        return JsonResponse({'status':'already_completed'})
    order.status = 'completed'
    order.completed_at = timezone.now()
    order.save(update_fields=['status','completed_at'])
    return JsonResponse({'status':'ok'})


@require_GET
def api_orders_completed(request: HttpRequest):
    """Return completed orders for a given date (default today).

    Query params:
      - date: optional, ISO date YYYY-MM-DD. Defaults to today in server TZ.
    Response: { orders: [ { id, created_at, completed_at, total_gross, payment_method, crew_id, lines:[...] }, ... ] }
    """
    from .models import Order
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            return JsonResponse({'error': 'Invalid date format, expected YYYY-MM-DD'}, status=400)
    else:
        target_date = timezone.now().date()

    orders = []
    qs = Order.objects.filter(status='completed', completed_at__date=target_date).order_by('-completed_at').prefetch_related('lines')
    for o in qs:
        orders.append({
            'id': o.id,
            'created_at': o.created_at.isoformat(),
            'completed_at': o.completed_at.isoformat() if o.completed_at else None,
            'total_gross': o.total_gross,
            'payment_method': o.payment_method,
            'crew_id': o.crew_id,
            'lines': [
                {
                    'name': l.name,
                    'qty': l.qty,
                    'variant': l.variant_label,
                    'meal': l.is_meal,
                    'meta': l.meta
                } for l in o.lines.all()
            ]
        })
    return JsonResponse({'date': str(target_date), 'orders': orders})
