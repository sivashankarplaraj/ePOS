import json
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
from urllib.error import URLError, HTTPError
from http.cookiejar import CookieJar
from pathlib import Path
from datetime import datetime
import csv

BASE = "http://127.0.0.1:8090"
_COOKIE_JAR = CookieJar()
_OPENER = build_opener(HTTPCookieProcessor(_COOKIE_JAR))


def _http_get(url: str) -> dict:
    req = Request(url)
    req.add_header("Accept", "application/json")
    with _OPENER.open(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    # Attach CSRF token from cookies if present
    token = None
    for c in _COOKIE_JAR:
        if c.name == 'csrftoken':
            token = c.value
            break
    if token:
        req.add_header('X-CSRFToken', token)
        req.add_header('Referer', f"{BASE}/manage_orders/app_prod_order/")
    with _OPENER.open(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _export_daily(outdir: Path):
    today = datetime.now().date().isoformat()
    # call management command via HTTP zip endpoint for simplicity
    # but it returns a zip; for strict PD/RV we invoke manage.py would be better; here we assume local path used
    # We'll fallback to subprocess if needed, but try direct manage.py call in tests/e2e instead
    return today


def test_submit_minimal_orders_via_api_and_export(tmp_path: Path):
    # Sanity: ensure server is up
    try:
        cat = _http_get(f"{BASE}/api/menu/categories?band=1")
    except Exception as e:
        import pytest
        pytest.skip(f"Server not reachable: {e}")

    # Prime cookies by visiting the app page (ensures csrftoken is set)
    opener = _OPENER.open(f"{BASE}/manage_orders/app_prod_order/")
    opener.read(); opener.close()

    # 1) Build a simple combo order for code 4 if exists
    combo_code = 4
    combo_detail = _http_get(f"{BASE}/api/item/combos/{combo_code}/detail?band=1") if False else _http_get(f"{BASE}/api/item/combo/{combo_code}/detail?band=1")
    combo_item = combo_detail.get("item", {})
    combo_price = int(combo_item.get("price_gross", 0) or 0)
    free_choices = []
    for grp in combo_item.get("free_choice_groups", []):
        opts = grp.get("options", [])
        if opts:
            free_choices.append(int(opts[0].get("code")))
    payload_combo = {
        "price_band": "1",
        "vat_basis": "take",
        "show_net": False,
        "payment_method": "Cash",
        "crew_id": "0",
        "lines": [
            {
                "code": combo_code,
                "type": "combo",
                "name": combo_item.get("name", "Combo 4"),
                "qty": 1,
                "price_gross": combo_price,
                "meta": {"free_choices": free_choices}
            }
        ]
    }
    _http_post(f"{BASE}/api/order/submit", payload_combo)

    # 2) Crew Food cheeseburger (code 3)
    prod3 = _http_get(f"{BASE}/api/item/product/3/detail?band=1").get("item", {})
    payload_staff = {
        "price_band": "1",
        "vat_basis": "take",
        "payment_method": "Crew Food",
        "crew_id": "123",
        "show_net": False,
        "lines": [
            {"code": 3, "type": "product", "name": prod3.get("name","Cheeseburger"), "qty": 1, "price_gross": int(prod3.get("price_gross",0) or 0)}
        ]
    }
    _http_post(f"{BASE}/api/order/submit", payload_staff)

    # 3) Waste food hamburger (code 1)
    prod1 = _http_get(f"{BASE}/api/item/product/1/detail?band=1").get("item", {})
    payload_waste = {
        "price_band": "1",
        "vat_basis": "take",
        "payment_method": "Waste food",
        "crew_id": "0",
        "show_net": False,
        "lines": [
            {"code": 1, "type": "product", "name": prod1.get("name","Hamburger"), "qty": 1, "price_gross": int(prod1.get("price_gross",0) or 0)}
        ]
    }
    _http_post(f"{BASE}/api/order/submit", payload_waste)

    # Export and validate PD/RV via management command
    import subprocess
    outdir = tmp_path / "exports"
    outdir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().date().isoformat()
    subprocess.check_call([r".venv\Scripts\python.exe", "manage.py", "export_daily_csvs", "--date", today, "--outdir", str(outdir)])
    ddmmyy = datetime.now().strftime("%d%m%y")
    pd_fp = outdir / f"PD{ddmmyy}.CSV"
    rv_fp = outdir / f"RV{ddmmyy}.CSV"
    assert pd_fp.exists() and rv_fp.exists()
    with pd_fp.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    ch_row = next((r for r in rows[1:] if r[0]=="3" and r[1]=="FALSE"), None)
    hb_row = next((r for r in rows[1:] if r[0]=="1" and r[1]=="FALSE"), None)
    assert ch_row is not None and hb_row is not None
    take, eat, waste, staff = map(int, ch_row[2:6])
    assert staff >= 1 and take == 0 and eat == 0
    take2, eat2, waste2, staff2 = map(int, hb_row[2:6])
    assert waste2 >= 1 and take2 == 0 and eat2 == 0
