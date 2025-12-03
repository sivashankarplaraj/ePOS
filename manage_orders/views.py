from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from update_till.models import (
    PdItem, AppProd, GroupTb, PChoice, CombTb, AppComb, PdVatTb, CompPro, OptPro,
    EposGroup, EposProd, EposFreeProd, EposComb, EposCombFreeProd, ToppingDel, ACodes,
    EposAddOns, PriceBand
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

@require_GET
def api_channel_mappings(request: HttpRequest):
        """Return active channels sourced from PriceBand with mapped fields.

        Mapping:
            name  <- SUPPLIER_NAME
            band  <- PRICE_ID
            channel_code <- SUPPLIER_CODE
            co_number <- PARENT_ID (coerced to string)
            is_third_party_delivery <- NOT of (HOT_DRINK)
        accept flags <- ACCEPT_* booleans on PriceBand

        Response:
        { "channels": [ { id, name, band, channel_code, co_number, is_third_party_delivery,
                   accept_cash, accept_card, accept_onacc, accept_voucher, accept_crew_food, accept_cooked_waste }, ... ] }
        """
        rows = PriceBand.objects.filter(APPLY_HERE=True).order_by('SEQ_ORDER', 'SUPPLIER_NAME')
        data = []
        for r in rows:
                data.append({
                        'id': getattr(r, 'REC_ID', None) or None,
                        'name': r.SUPPLIER_NAME,
                        'band': r.PRICE_ID,
                        'channel_code': r.SUPPLIER_CODE,
                        'co_number': str(r.PARENT_ID) if r.PARENT_ID is not None else '',
                        'is_third_party_delivery': not bool(r.HOT_DRINK),
            'accept_cash': bool(getattr(r, 'ACCEPT_CASH', False)),
            'accept_card': bool(getattr(r, 'ACCEPT_CARD', False)),
            'accept_onacc': bool(getattr(r, 'ACCEPT_ONACC', False)),
            'accept_voucher': bool(getattr(r, 'ACCEPT_VOUCHER', False)),
            'accept_crew_food': bool(getattr(r, 'ACCEPT_CREW_FOOD', False)),
            'accept_cooked_waste': bool(getattr(r, 'ACCEPT_COOKED_WASTE', False)),
                })
        return JsonResponse({'channels': data})

@ensure_csrf_cookie
def index(request):    
    # return app_prod_order.html template
    return render(request, 'manage_orders/app_prod_order.html')

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

@ensure_csrf_cookie
def reports(request):
    # Use superuser flag for privileged report export controls
    return render(request, 'manage_orders/reports.html', {'is_superuser': getattr(request.user, 'is_superuser', False)})

@ensure_csrf_cookie
def kitchen_monitor(request):
    """Simple kitchen monitor page (initial placeholder)."""
    return render(request, 'manage_orders/kitchen_monitor.html')

@ensure_csrf_cookie
def customer_basket(request):
    """Customer-facing basket display that mirrors the POS basket in real time."""
    return render(request, 'manage_orders/customer_basket.html')

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
    # Prefer ITEM_DESC from EposProd if available; fallback to PdItem.PRODNAME
    disp_name = (item.PRODNAME or '').strip()
    try:
        ep = EposProd.objects.filter(PRODNUMB=item.PRODNUMB).order_by('-last_updated').first()
        if ep and (ep.ITEM_DESC or '').strip():
            disp_name = ep.ITEM_DESC.strip()
    except Exception:
        pass

    data = {
        'type': 'product',
        'code': item.PRODNUMB,
        'name': disp_name,
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
    # Meal classification from AppProd:
    # MEAL_ID = 1 => Regular Meal, MEAL_ID = 2 => Kids Meal
    if app_meta:
        meal_id = int(getattr(app_meta, 'MEAL_ID', 0) or 0)
        meal_type = 'regular' if meal_id == 1 else ('kids' if meal_id == 2 else None)
        data['meal_id'] = meal_id
        data['meal_type'] = meal_type
        data['meal_flag'] = meal_type is not None
        # Double / triple variants
        variant_codes = []
        if app_meta.DOUBLE_PDNUMB and app_meta.DOUBLE_PDNUMB != 0:
            variant_codes.append(('double', app_meta.DOUBLE_PDNUMB))
        if app_meta.TRIPLE_PDNUMB and app_meta.TRIPLE_PDNUMB != 0:
            variant_codes.append(('triple', app_meta.TRIPLE_PDNUMB))
        # Look up variants only once (caller may supply pre-fetched map)
        for label, vcode in variant_codes:
            # variant product may not exist in PdItem table (skip if not)
            vitem = PdItem.objects.filter(PRODNUMB=vcode).only('PRODNUMB', 'PRODNAME', std_col, dc_col).first()
            if vitem:
                v_std = getattr(vitem, std_col, 0) or 0
                v_dc = getattr(vitem, dc_col, 0) or 0
                # Prefer ITEM_DESC from EposProd for variant name; fallback to PdItem.PRODNAME
                v_name = (getattr(vitem, 'PRODNAME', '') or '').strip()
                try:
                    v_ep = EposProd.objects.filter(PRODNUMB=vitem.PRODNUMB).order_by('-last_updated').first()
                    if v_ep and (v_ep.ITEM_DESC or '').strip():
                        v_name = v_ep.ITEM_DESC.strip()
                except Exception:
                    pass
                data['variants'].append({
                    'label': label,
                    'code': vitem.PRODNUMB,
                    'name': v_name,
                    'price_gross': int(v_std),
                    'discounted_price_gross': int(v_dc) if v_dc else 0
                })
    else:
        data['meal_flag'] = False
        data['meal_id'] = 0
        data['meal_type'] = None
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
    # Prefer ITEM_DESC from EposComb if available; fallback to CombTb.DESC
    combo_name = (combo.DESC or '').strip()
    try:
        ec = EposComb.objects.filter(COMBONUMB=combo.COMBONUMB).order_by('-last_updated').first()
        if ec and (ec.ITEM_DESC or '').strip():
            combo_name = ec.ITEM_DESC.strip()
    except Exception:
        pass

    data = {
        'type': 'combo',
        'code': combo.COMBONUMB,
        'name': combo_name,
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
def api_menu_categories(request: HttpRequest):
    """Return only the list of menu categories for a given price band.

    Query params:
        band: required (1..6)
        include_empty: optional (1/true)

    Response: { "band": "1", "categories": [ { id, name, source_type, meal_group, item_count }, ... ] }
    """
    band = request.GET.get('band')
    if band not in {'1','2','3','4','5','6'}:
        return JsonResponse({'error': 'Invalid or missing band'}, status=400)
    include_empty = request.GET.get('include_empty', '').lower() in {'1','true','yes'}

    # New source: EposGroup / EposProd / EposComb mapping. Keep response shape stable.
    # Count products per EPOS_GROUP_ID from EposProd.
    prod_counts: dict[int, int] = {}
    for ep in EposProd.objects.all().only('EPOS_GROUP'):
        prod_counts[ep.EPOS_GROUP] = prod_counts.get(ep.EPOS_GROUP, 0) + 1
    # Count combos per EPOS_GROUP from EposComb (e.g. Special Offers group 9)
    combo_counts: dict[int, int] = {}
    for ec in EposComb.objects.all().only('EPOS_GROUP'):
        combo_counts[ec.EPOS_GROUP] = combo_counts.get(ec.EPOS_GROUP, 0) + 1

    categories = []
    epos_groups = list(EposGroup.objects.all().order_by('EPOS_GROUP_ID'))
    for grp in epos_groups:
        prod_count = prod_counts.get(grp.EPOS_GROUP_ID, 0)
        comb_count = combo_counts.get(grp.EPOS_GROUP_ID, 0)
        total = prod_count + comb_count
        if total or include_empty:
            categories.append({
                'id': grp.EPOS_GROUP_ID,  # maintain 'id' key expected by frontend
                'name': (grp.EPOS_GROUP_TITLE or '').strip(),
                'source_type': 'P',  # legacy field retained for frontend
                'meal_group': 0,     # placeholder (legacy compatibility)
                'item_count': total,
                'has_combos': comb_count > 0,
            })
    # Fallback: if no EPOS groups found (e.g., initial data load), use legacy GroupTb categories so the UI can render.
    if not categories:
        for grp in GroupTb.objects.all().order_by('GROUP_ID'):
            if include_empty or True:
                categories.append({
                    'id': grp.GROUP_ID,
                    'name': (grp.GROUP_NAME or '').strip(),
                    'source_type': grp.SOURCE_TYPE,
                    'meal_group': grp.MEAL_GROUP,
                    'item_count': 0,
                    'has_combos': False,
                })
    return JsonResponse({'band': band, 'categories': categories})


@require_GET
def api_category_items(request: HttpRequest, group_id: int):
    """Return items (products + combos) for a single category/group for a given band.

    Query params:
        band: required (1..6)
    Response: { "band": "1", "category": { id, name }, "items": [ {..}, ... ] }
    """
    band = request.GET.get('band')
    if band not in {'1','2','3','4','5','6'}:
        return JsonResponse({'error': 'Invalid or missing band'}, status=400)

    vat_rates = _vat_rate_map()

    grp = EposGroup.objects.filter(EPOS_GROUP_ID=group_id).first()
    if not grp:
        return JsonResponse({'error': 'Category not found'}, status=404)

    # Fetch ePOS products for this group ordered by EPOS_SEQUENCE
    epos_products = list(
        EposProd.objects.filter(EPOS_GROUP=group_id)
        .only('PRODNUMB', 'EPOS_GROUP', 'EPOS_SEQUENCE', 'COLOUR_RED', 'COLOUR_GREEN', 'COLOUR_BLUE', 'ITEM_DESC')
        .order_by('EPOS_SEQUENCE')
    )
    prod_nums = [p.PRODNUMB for p in epos_products]
    pd_items_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=prod_nums)}
    app_prod_meta = {ap.PRODNUMB: ap for ap in AppProd.objects.filter(PRODNUMB__in=prod_nums)}

    items: list[dict] = []
    # Preload defaults for kids meal preview (fries and kids drinks)
    std_col = _price_column_name(band, discounted=False)
    dc_col = _price_column_name(band, discounted=True)
    fries_list = list(PdItem.objects.filter(PRODNUMB__in=[30, 31]).only('PRODNUMB', std_col, dc_col, 'TAKE_VAT_CLASS', 'EAT_VAT_CLASS'))
    kids_drink_codes = list(EposProd.objects.filter(EPOS_GROUP=99).values_list('PRODNUMB', flat=True))
    kids_drinks_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=kids_drink_codes).only('PRODNUMB', std_col, dc_col, 'TAKE_VAT_CLASS', 'EAT_VAT_CLASS')}

    def comp_price(it):
        if not it:
            return 0
        dc = getattr(it, dc_col, None) or 0
        std = getattr(it, std_col, None) or 0
        return int(dc) if dc and int(dc) > 0 else int(std)

    def comp_net(it, gross: int, basis: str) -> int:
        if not it or not gross:
            return 0
        vat_class = getattr(it, 'EAT_VAT_CLASS' if basis == 'eat' else 'TAKE_VAT_CLASS', None)
        rate = vat_rates.get(vat_class, 0.0)
        try:
            return int(round(gross / (1 + (rate/100.0))))
        except ZeroDivisionError:
            return gross
    for ep in epos_products:
        pd_item = pd_items_map.get(ep.PRODNUMB)
        if not pd_item:
            continue
        prod_obj = _serialize_product(pd_item, band, app_meta=app_prod_meta.get(ep.PRODNUMB), vat_rates=vat_rates)
        # Attach EPOS group id for frontend policy (e.g., kids = group 4)
        prod_obj['epos_group_id'] = group_id
        # If Kids Meal (meal_id==2), compute a preview meal price for display: burger + default fries + default kids drink
        try:
            if int(prod_obj.get('meal_id') or 0) == 2:
                # Burger component price used in meal: discounted if available else standard
                burger_price = comp_price(pd_item)
                # Default fries: pick the lowest priced meal component among available fries
                fries_price = 0
                fries_choice = None
                if fries_list:
                    fries_choice = min(fries_list, key=lambda f: comp_price(f))
                    fries_price = comp_price(fries_choice)
                # Default kids drink: pick the lowest priced among kids drinks
                drink_price = 0
                drink_choice = None
                if kids_drinks_map:
                    drink_choice = min(kids_drinks_map.values(), key=lambda d: comp_price(d))
                    drink_price = comp_price(drink_choice)
                meal_gross = int((burger_price or 0) + (fries_price or 0) + (drink_price or 0))
                # Compute preview net values by summing per-component net for both bases
                take_net = 0
                eat_net = 0
                if meal_gross:
                    take_net = (
                        comp_net(pd_item, burger_price, 'take') +
                        comp_net(fries_choice, fries_price, 'take') +
                        comp_net(drink_choice, drink_price, 'take')
                    )
                    eat_net = (
                        comp_net(pd_item, burger_price, 'eat') +
                        comp_net(fries_choice, fries_price, 'eat') +
                        comp_net(drink_choice, drink_price, 'eat')
                    )
                prod_obj['kids_meal_price_gross'] = meal_gross
                prod_obj['kids_meal_price_net_take'] = int(take_net)
                prod_obj['kids_meal_price_net_eat'] = int(eat_net)
        except Exception:
            # If any issue in preview computation, skip silently
            pass
        # Attach RGB colour from EposProd if present
        try:
            r = int(getattr(ep, 'COLOUR_RED', 0) or 0)
            g = int(getattr(ep, 'COLOUR_GREEN', 0) or 0)
            b = int(getattr(ep, 'COLOUR_BLUE', 0) or 0)
            # Normalize into 0..255 bounds just in case
            r = max(0, min(255, r)); g = max(0, min(255, g)); b = max(0, min(255, b))
            prod_obj['colour'] = {'r': r, 'g': g, 'b': b}
        except Exception:
            # If any issue, skip colour attachment (frontend falls back to hashed accent)
            pass
        items.append(prod_obj)

    # Add combination products from EposComb for this group (e.g., Special Offers / group 9)
    epos_combos = list(EposComb.objects.filter(EPOS_GROUP=group_id).order_by('EPOS_SEQUENCE'))
    if epos_combos:
        # Map COMBONUMB to CombTb to pull pricing/VAT where available
        comb_details = {c.COMBONUMB: c for c in CombTb.objects.filter(COMBONUMB__in=[ec.COMBONUMB for ec in epos_combos])}
        for ec in epos_combos:
            detail = comb_details.get(ec.COMBONUMB)
            if detail:
                combo_obj = _serialize_combo(detail, band, vat_rates=vat_rates)
                combo_obj['epos_group_id'] = group_id
                items.append(combo_obj)
            else:
                # Fallback minimal serialization (price 0 if no CombTb pricing row)
                items.append({
                    'type': 'combo',
                    'code': ec.COMBONUMB,
                    'name': (ec.DESC or '').strip(),
                    'band': band,
                    'price_gross': 0,
                    'price_net_take': 0,
                    'price_net_eat': 0,
                    'take_vat_rate': 0.0,
                    'eat_vat_rate': 0.0,
                    'variants': [],
                    'meal_flag': False,
                    'has_discount': False,
                    'epos_group_id': group_id
                })
    # Keep insertion order: products then combos (mirrors legacy behaviour)
    return JsonResponse({
        'band': band,
        'category': {'id': grp.EPOS_GROUP_ID, 'name': (grp.EPOS_GROUP_TITLE or '').strip()},
        'items': items
    })


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


@require_GET
def api_product_toppings(request: HttpRequest, prod_code: int):
    """Return list of topping MENU_DESC values for a given product code.

    This joins ACodes (product -> stock component) to ToppingDel (topping metadata).
    Response JSON:
      { "product": <int>, "toppings": [ { "acode": <int>, "desc": str, "menu_desc": str } ... ],
        "menu_desc_joined": "A, B, C" }
    If none found returns empty list.
    """
    # Fetch ACodes rows for the product
    a_rows = list(ACodes.objects.filter(PRODNUMB=prod_code).only('ST_CODENUM'))
    if not a_rows:
        return JsonResponse({'product': prod_code, 'toppings': [], 'menu_desc_joined': ''})
    acode_nums = [a.ST_CODENUM for a in a_rows]
    # Get toppings metadata
    trows = {t.ACODE: t for t in ToppingDel.objects.filter(ACODE__in=acode_nums)}
    toppings = []
    for st_code in acode_nums:
        t = trows.get(st_code)
        if not t:
            continue
        toppings.append({
            'acode': t.ACODE,
            'desc': (t.DESC or '').strip(),
            'menu_desc': (t.MENU_DESC or '').strip()
        })
    joined = ', '.join([tp['menu_desc'] for tp in toppings if tp['menu_desc']])
    return JsonResponse({'product': prod_code, 'toppings': toppings, 'menu_desc_joined': joined})


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
        # Attach EPOS group id where known (used by frontend to enforce kids meal policy)
        try:
            ep_meta = EposProd.objects.filter(PRODNUMB=code).only('EPOS_GROUP').first()
            if ep_meta:
                base['epos_group_id'] = ep_meta.EPOS_GROUP
        except Exception:
            pass
        # Options from PChoice
        opt_links = PChoice.objects.filter(PRODNUMB=code)
        opt_codes = [o.OPT_PRODNUMB for o in opt_links]
        opt_items = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=opt_codes)}
        base['options'] = []
        for c in opt_codes:
            p = opt_items.get(c)
            if p:
                base['options'].append(_serialize_product(p, band, vat_rates=vat_rates))
        # Meal components heuristic:
        # - Fries: fixed codes [30, 31] for now
        # - Drinks: for Kids Meals, restrict to Kids Drinks list derived from EposProd where EPOS_GROUP = 99
        #           otherwise use all drinks where MEAL_DRINK > 0
        meal_components = []
        if base.get('meal_flag'):
            fries = PdItem.objects.filter(PRODNUMB__in=[30,31])
            # Detect if this product is a Kids item via ePOS group title or name pattern
            is_kids = False
            try:
                ep = EposProd.objects.filter(PRODNUMB=code).only('EPOS_GROUP').first()
                if ep:
                    grp = EposGroup.objects.filter(EPOS_GROUP_ID=ep.EPOS_GROUP).only('EPOS_GROUP_TITLE').first()
                    if grp and 'kid' in (grp.EPOS_GROUP_TITLE or '').lower():
                        is_kids = True
            except Exception:
                pass
            # Additional fallback: product name contains 'kid'
            if not is_kids and 'kid' in (base.get('name','')).lower():
                is_kids = True
            # Build drinks ordered by EPOS_SEQUENCE from EposProd
            drinks_items: list[PdItem] = []
            if is_kids:
                # Kids Drinks are ePOS products in group 99; order by EPOS_SEQUENCE
                ordered_codes = list(
                    EposProd.objects.filter(EPOS_GROUP=99)
                    .order_by('EPOS_SEQUENCE')
                    .values_list('PRODNUMB', flat=True)
                )
                pd_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=ordered_codes)}
                drinks_items = [pd_map[c] for c in ordered_codes if c in pd_map]
                # Fallback: if any kids drinks exist in PdItem but not in EposProd, append them at end by PRODNUMB
                remaining_codes = set(PdItem.objects.filter(PRODNUMB__in=ordered_codes).values_list('PRODNUMB', flat=True)) - set(pd_map.keys())
                if remaining_codes:
                    extra_items = list(PdItem.objects.filter(PRODNUMB__in=list(remaining_codes)).order_by('PRODNUMB'))
                    drinks_items.extend(extra_items)
            else:
                # All meal-eligible drinks (MEAL_DRINK > 0), ordered by EposProd.EPOS_SEQUENCE where available
                drink_codes = list(PdItem.objects.filter(MEAL_DRINK__gt=0).values_list('PRODNUMB', flat=True))
                if drink_codes:
                    ordered_codes = list(
                        EposProd.objects.filter(PRODNUMB__in=drink_codes)
                        .order_by('EPOS_SEQUENCE')
                        .values_list('PRODNUMB', flat=True)
                    )
                    pd_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=ordered_codes)}
                    drinks_items = [pd_map[c] for c in ordered_codes if c in pd_map]
                    # Append any remaining MEAL_DRINK>0 PdItems that don't have an EposProd row, sorted by PRODNUMB
                    remaining = set(drink_codes) - set(pd_map.keys())
                    if remaining:
                        extra_items = list(PdItem.objects.filter(PRODNUMB__in=list(remaining)).order_by('PRODNUMB'))
                        drinks_items.extend(extra_items)
            meal_components = {
                'fries': [_serialize_product(f, band, vat_rates=vat_rates) for f in fries],
                'drinks': [_serialize_product(d, band, vat_rates=vat_rates) for d in drinks_items],
            }
        base['meal_components'] = meal_components
        # Free choice groups (EposFreeProd): each row may define FREE_CHOICE_1 / FREE_CHOICE_2 as comma lists.
        free_rows = list(EposFreeProd.objects.filter(PRODNUMB=code))
        free_choice_groups = []
        if free_rows:
            # Collect all codes to batch load pricing names
            all_codes: set[int] = set()
            parsed_groups: list[tuple[int, list[int]]] = []
            for fr in free_rows:
                for idx, field in enumerate(['FREE_CHOICE_1','FREE_CHOICE_2'], start=1):
                    raw = getattr(fr, field, '') or ''
                    if not raw.strip():
                        continue
                    codes: list[int] = []
                    for part in raw.split(','):
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            val = int(part)
                        except Exception:
                            continue
                        codes.append(val)
                        all_codes.add(val)
                    if codes:
                        parsed_groups.append((idx, codes))
            if parsed_groups:
                pd_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=list(all_codes))}
                for order_index, codes in parsed_groups:
                    opts = []
                    for c in codes:
                        p = pd_map.get(c)
                        if p:
                            opts.append(_serialize_product(p, band, vat_rates=vat_rates))
                    if opts:
                        free_choice_groups.append({
                            'group': order_index,
                            'free_count': 1,  # exactly one free from the list
                            'options': opts
                        })
        base['free_choice_groups'] = free_choice_groups
        # Add-ons (EposAddOns): parse comma-separated codes and serialize with current band pricing
        addons_list: list[dict] = []
        try:
            ao = EposAddOns.objects.filter(PRODNUMB=code).order_by('-last_updated').first()
            raw = (ao.ADD_ONS if ao and ao.ADD_ONS else '')
            codes: list[int] = []
            for part in str(raw).split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    codes.append(int(part))
                except Exception:
                    continue
            if codes:
                pd_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=codes)}
                for c in codes:
                    p = pd_map.get(c)
                    if p:
                        addons_list.append(_serialize_product(p, band, vat_rates=vat_rates))
        except Exception:
            addons_list = []
        base['addons'] = addons_list
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
        # Free choice groups for combo (EposCombFreeProd) mirroring product free choices
        free_rows = list(EposCombFreeProd.objects.filter(COMBONUMB=code))
        free_choice_groups = []
        if free_rows:
            all_codes: set[int] = set()
            parsed_groups: list[tuple[int, list[int]]] = []
            for fr in free_rows:
                for idx, field in enumerate(['FREE_CHOICE_1','FREE_CHOICE_2'], start=1):
                    raw = getattr(fr, field, '') or ''
                    if not raw.strip():
                        continue
                    codes: list[int] = []
                    for part in raw.split(','):
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            val = int(part)
                        except Exception:
                            continue
                        codes.append(val)
                        all_codes.add(val)
                    if codes:
                        parsed_groups.append((idx, codes))
            if parsed_groups:
                pd_map = {p.PRODNUMB: p for p in PdItem.objects.filter(PRODNUMB__in=list(all_codes))}
                for order_index, codes in parsed_groups:
                    opts = []
                    for c in codes:
                        p = pd_map.get(c)
                        if p:
                            opts.append(_serialize_product(p, band, vat_rates=vat_rates))
                    if opts:
                        free_choice_groups.append({
                            'group': order_index,
                            'free_count': 1,
                            'options': opts
                        })
        base['free_choice_groups'] = free_choice_groups
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
    band_co_number = (payload.get('band_co_number') or '').strip()[:30]
    # Lightweight validation: allow empty or must match one of known SUPPLIER_NAMEs from active PriceBand rows
    if band_co_number:
        allowed_names = set()
        # Dynamic names from PriceBand (APPLY_HERE only)
        for pb in PriceBand.objects.filter(APPLY_HERE=True).only('SUPPLIER_NAME'):
            if pb.SUPPLIER_NAME:
                allowed_names.add(pb.SUPPLIER_NAME.strip())
        if band_co_number not in allowed_names:
            return JsonResponse({'error': 'Invalid band_co_number (supplier name)'}, status=400)
    vat_basis = payload.get('vat_basis')
    if vat_basis not in {'take','eat'}:
        return JsonResponse({'error': 'Invalid vat_basis'}, status=400)
    lines = payload.get('lines') or []
    # Optional payment details (from checkout modal)
    payment_method = (payload.get('payment_method') or 'Cash').strip()
    crew_id = str(payload.get('crew_id') or '0').strip()
    if crew_id == '':
        return JsonResponse({'error': 'Crew ID is required'}, status=400)
    # Optional order notes (limited length)
    notes = (payload.get('notes') or '').strip()
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
            band_co_number=band_co_number,
            notes=notes[:1000]
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
        # Handle Split Pay breakdown if supplied
        if payment_method.lower() == 'split':
            try:
                split_cash = int(payload.get('split_cash_pence') or 0)
                split_card = int(payload.get('split_card_pence') or 0)
            except Exception:
                split_cash = 0; split_card = 0
            # Validate non-negative and sum equals total_gross
            if split_cash < 0 or split_card < 0 or (split_cash + split_card) != total_gross:
                return JsonResponse({'error': 'Invalid split amounts: Cash + Card must equal total and be non-negative'}, status=400)
            order.split_cash_pence = split_cash
            order.split_card_pence = split_card
            order.save(update_fields=['total_gross','total_net','split_cash_pence','split_card_pence'])
        else:
            order.save(update_fields=['total_gross','total_net'])
    return JsonResponse({'order_id': order.id, 'total_gross': total_gross})


@require_GET
def api_orders_summary(request: HttpRequest):
    from .models import Order
    today = timezone.now().date()
    qs = Order.objects.filter(created_at__date=today)
    preparing = qs.filter(status='preparing').count()
    packed = qs.filter(status='packed').count()
    # Count dispatched (strict)
    dispatched = qs.filter(status='dispatched').count()
    return JsonResponse({'date': str(today), 'preparing': preparing, 'packed': packed, 'dispatched': dispatched})


@require_GET
def api_orders_pending(request: HttpRequest):
    from .models import Order
    today = timezone.now().date()
    orders = []
    for o in Order.objects.filter(status__in=['preparing','packed'], created_at__date=today).order_by('created_at').prefetch_related('lines'):
        orders.append({
            'id': o.id,
            'created_at': o.created_at.isoformat(),
            'age_seconds': int((timezone.now()-o.created_at).total_seconds()),
            'status': o.status,
            'payment_method': o.payment_method,
            'band_co_number': o.band_co_number,
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
            ],
            'notes': o.notes
        })
    return JsonResponse({'orders': orders})


@require_POST
def api_order_complete(request: HttpRequest, order_id: int):
    from .models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error':'Not found'}, status=404)
    # If already dispatched, no-op
    if order.status == 'dispatched':
        return JsonResponse({'status':'already_dispatched'})
    # Optionally enforce valid transition (allow from preparing or packed)
    if order.status not in {'preparing', 'packed'}:
        return JsonResponse({'error': 'Invalid state transition'}, status=400)
    order.status = 'dispatched'
    order.completed_at = timezone.now()
    order.save(update_fields=['status','completed_at'])
    return JsonResponse({'status':'ok'})


@require_POST
def api_order_pack(request: HttpRequest, order_id: int):
    from .models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error':'Not found'}, status=404)
    if order.status == 'packed':
        return JsonResponse({'status': 'already_packed'})
    if order.status not in {'preparing','packed'}:
        return JsonResponse({'error': 'Invalid state transition'}, status=400)
    order.status = 'packed'
    order.packed_at = timezone.now()
    order.save(update_fields=['status','packed_at'])
    return JsonResponse({'status': 'ok'})


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
    # Only dispatched orders for the date
    qs = Order.objects.filter(status='dispatched', completed_at__date=target_date).order_by('-completed_at').prefetch_related('lines')
    for o in qs:
        orders.append({
            'id': o.id,
            'created_at': o.created_at.isoformat(),
            'packed_at': o.packed_at.isoformat() if o.packed_at else None,
            'completed_at': o.completed_at.isoformat() if o.completed_at else None,
            'total_gross': o.total_gross,
            'payment_method': o.payment_method,
            'band_co_number': o.band_co_number,
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


@require_GET
def api_daily_sales(request: HttpRequest):
    """Return total sales (gross) and breakdown by payment_method for a given date.

    Query params:
      - date: optional ISO date (YYYY-MM-DD); defaults to today (server TZ)

    Response JSON:
      { "date": "YYYY-MM-DD", "total_gross": 12345, "currency": "GBP", "payment_methods": [ {"method": "Cash", "total_gross": 1000}, ... ] }

    All monetary values are integer pence (aligning with Order.total_gross storage). Frontend can divide by 100 for £ display.
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

    # Use dispatched orders completed on the target date for sales reporting
    qs = Order.objects.filter(status='dispatched', completed_at__date=target_date)
    # Aggregate totals grouped by payment_method; treat blank as 'Unspecified'
    from collections import defaultdict
    by_method: dict[str, int] = defaultdict(int)
    total = 0
    for o in qs.only('total_gross', 'payment_method'):
        m = (o.payment_method or '').strip() or 'Unspecified'
        by_method[m] += o.total_gross
        total += o.total_gross
    breakdown = [
        {'method': m, 'total_gross': amt} for m, amt in sorted(by_method.items(), key=lambda x: (-x[1], x[0]))
    ]
    return JsonResponse({'date': str(target_date), 'total_gross': total, 'currency': 'GBP', 'payment_methods': breakdown})


@require_GET
def api_daily_sales_hourly(request: HttpRequest):
    """Return hourly breakdown of orders for a given date.

    Response:
      { "date": "YYYY-MM-DD", "hours": [ {"hour":0, "order_count": 3, "total_gross": 1234}, ..., {"hour":23,...} ] }
    Hours are 0-23 inclusive. Missing hours have zero counts.
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
    # Filter orders on that date
    # Use dispatched orders completed on the target date for hourly reporting
    qs = Order.objects.filter(status='dispatched', completed_at__date=target_date).only('completed_at','total_gross')
    buckets = {h: {'hour': h, 'order_count': 0, 'total_gross': 0} for h in range(24)}
    for o in qs:
        h = o.completed_at.hour
        b = buckets.get(h)
        if b:
            b['order_count'] += 1
            b['total_gross'] += o.total_gross
    ordered = [buckets[h] for h in range(24)]
    return JsonResponse({'date': str(target_date), 'hours': ordered})


@require_POST
def api_paid_out(request: HttpRequest):
    """Record a cash Paid Out event as an Order with no lines.

    Expected JSON body:
      { "price_band":"1"|"5", "band_co_number": "<SUPPLIER_NAME>", "amount_pence": 1234, "notes": "..." }

            Server behavior:
                - Creates an Order with created_at/packed_at/completed_at = now, status = dispatched
                - vat_basis = 'eat', show_net = False
                - payment_method = 'Paid Out'
                - total_gross = amount_pence (cash leaving till)
                - total_net = 0
                - price_band must be '1' or '5'
                - band_co_number validated against active PriceBand.SUPPLIER_NAMEs
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    band = str(payload.get('price_band'))
    if band not in {'1','5'}:
        return JsonResponse({'error': 'Paid Out allowed only for Standard bands 1 or 5'}, status=400)
    band_co_number = (payload.get('band_co_number') or '').strip()[:30]
    # Validate band CO using SUPPLIER_NAME from active PriceBand rows
    if band_co_number:
        allowed_names = set()
        for pb in PriceBand.objects.filter(APPLY_HERE=True).only('SUPPLIER_NAME'):
            if pb.SUPPLIER_NAME:
                allowed_names.add(pb.SUPPLIER_NAME.strip())
        if band_co_number not in allowed_names:
            return JsonResponse({'error': 'Invalid band_co_number (supplier name)'}, status=400)
    try:
        amount_pence = int(payload.get('amount_pence'))
    except Exception:
        return JsonResponse({'error': 'Invalid amount_pence'}, status=400)
    if amount_pence <= 0:
        return JsonResponse({'error': 'amount_pence must be > 0'}, status=400)
    notes = (payload.get('notes') or '').strip()
    from .models import Order
    now = timezone.now()
    with transaction.atomic():
        order = Order.objects.create(
            created_at=now,
            packed_at=now,
            completed_at=now,
            status='dispatched',
            price_band=int(band),
            vat_basis='eat',
            show_net=False,
            total_gross=int(amount_pence),
            total_net=0,
            payment_method='Paid Out',
            crew_id='0',
            band_co_number=band_co_number,
            notes=notes[:1000]
        )
    return JsonResponse({'status': 'ok', 'order_id': order.id})


@require_GET
@staff_member_required
def export_daily_csvs_zip(request: HttpRequest):
    """Generate daily CSVs (MP/PD/RV) via management command and return them zipped.

    Query params:
      - date: optional ISO date (YYYY-MM-DD); defaults to today.

    Response: application/zip with filename daily_csvs_<yyyymmdd>.zip
    Cleans up temporary files after streaming.
    """
    import io, zipfile, tempfile, os
    from django.core import management
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            return JsonResponse({'error': 'Invalid date format, expected YYYY-MM-DD'}, status=400)
    else:
        target_date = timezone.now().date()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run management command to produce CSV files in tmpdir
        management.call_command('export_daily_csvs', date=str(target_date), outdir=tmpdir, clear=True, verbosity=0)
        # Collect expected filenames
        mp = f"MP{target_date:%d%m%y}.CSV"
        pd = f"PD{target_date:%d%m%y}.CSV"
        rv = f"RV{target_date:%d%m%y}.CSV"
        kwk = "K_WK_VAT.csv"  # weekly VAT summary snapshot
        filenames = [mp, pd, rv, kwk]
        memfile = io.BytesIO()
        with zipfile.ZipFile(memfile, 'w', zipfile.ZIP_DEFLATED) as zf:
            for name in filenames:
                path = os.path.join(tmpdir, name)
                if os.path.exists(path):
                    zf.write(path, arcname=name)
        memfile.seek(0)
        resp = HttpResponse(memfile.read(), content_type='application/zip')
        resp['Content-Disposition'] = f'attachment; filename="daily_csvs_{target_date:%Y%m%d}.zip"'
        return resp
