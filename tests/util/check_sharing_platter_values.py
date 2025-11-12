import json
import csv
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar
from datetime import datetime
from pathlib import Path
import subprocess
import sys

BASE = "http://127.0.0.1:8090"
CJ = CookieJar()
OP = build_opener(HTTPCookieProcessor(CJ))


def http_get(url: str) -> dict:
    req = Request(url)
    req.add_header("Accept", "application/json")
    with OP.open(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    token = None
    for c in CJ:
        if c.name == 'csrftoken':
            token = c.value
            break
    if token:
        req.add_header('X-CSRFToken', token)
        req.add_header('Referer', f"{BASE}/manage_orders/app_prod_order/")
    with OP.open(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    # Prime cookies
    OP.open(f"{BASE}/manage_orders/app_prod_order/").close()

    # Export BEFORE snapshot
    outdir = Path(".tmp_exports")
    outdir.mkdir(exist_ok=True)
    today = datetime.now().date().isoformat()
    before_dir = outdir / "before"
    before_dir.mkdir(exist_ok=True)
    subprocess.check_call([sys.executable, "manage.py", "export_daily_csvs", "--date", today, "--outdir", str(before_dir)])
    ddmmyy = datetime.now().strftime("%d%m%y")
    rv_before_fp = before_dir / f"RV{ddmmyy}.CSV"
    with rv_before_fp.open(newline="", encoding="utf-8") as f:
        b_rows = list(csv.reader(f))
    b_header = b_rows[0]; b_vals = b_rows[1]
    b_idx = {k:i for i,k in enumerate(b_header)}
    b_disc = int(b_vals[b_idx['TDISCNTVA']])
    b_vat = int(b_vals[b_idx['VAT']])

    # Fetch combo 4 detail
    combo_code = 4
    combo_detail = http_get(f"{BASE}/api/item/combo/{combo_code}/detail?band=1")
    item = combo_detail.get("item", {})
    price_gross = int(item.get("price_gross", 0) or 0)

    # Choose free dips 27, 39 if available; else pick first two
    target_free = []
    available_free = []
    for grp in item.get("free_choice_groups", []):
        for opt in grp.get("options", []):
            try:
                available_free.append(int(opt.get("code")))
            except Exception:
                pass
    if 27 in available_free:
        target_free.append(27)
    if 39 in available_free:
        target_free.append(39)
    if len(target_free) < 2:
        # pad to 2 with available
        for c in available_free:
            if c not in target_free:
                target_free.append(c)
            if len(target_free) >= 2:
                break

    payload = {
        "price_band": "1",
        "vat_basis": "take",
        "show_net": False,
        "payment_method": "Cash",
        "crew_id": "0",
        "lines": [
            {
                "code": combo_code,
                "type": "combo",
                "name": item.get("name", "Sharing Platter"),
                "qty": 1,
                "price_gross": price_gross,
                "meta": {"free_choices": target_free}
            }
        ]
    }
    http_post(f"{BASE}/api/order/submit", payload)

    # Export AFTER snapshot
    after_dir = outdir / "after"
    after_dir.mkdir(exist_ok=True)
    subprocess.check_call([sys.executable, "manage.py", "export_daily_csvs", "--date", today, "--outdir", str(after_dir)])
    rv_after_fp = after_dir / f"RV{ddmmyy}.CSV"
    with rv_after_fp.open(newline="", encoding="utf-8") as f:
        a_rows = list(csv.reader(f))
    a_header = a_rows[0]; a_vals = a_rows[1]
    a_idx = {k:i for i,k in enumerate(a_header)}
    a_disc = int(a_vals[a_idx['TDISCNTVA']])
    a_vat = int(a_vals[a_idx['VAT']])

    # Delta produced by the single Sharing Platter order
    print(f"TDISCNTVA={a_disc - b_disc}")
    print(f"VAT={a_vat - b_vat}")


if __name__ == "__main__":
    main()
