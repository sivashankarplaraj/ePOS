from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from update_till.models import PdItem
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

def index(request):
    # Landing page could become a dashboard; for now redirect logic optional
    return order(request)

def order(request):
    context = {
        'price_band': _price_band_map(),
    }
    return render(request, 'manage_orders/order.html', context)


def _price_column_name(band: str, discounted: bool) -> str:
    """Return model field name for given band and discounted flag.

    band is a string '1'..'6' as produced by _price_band_map values.
    """
    base = 'DC_VATPR' if discounted else 'VATPR'
    return base if str(band) == '1' else f"{base}_{band}"


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
