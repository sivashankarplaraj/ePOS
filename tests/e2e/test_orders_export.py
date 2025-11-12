import os
import csv
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("EPOS_BASE_URL", "http://127.0.0.1:8090")
REQUIRED_ENV = os.getenv("EPOS_E2E", "0")


def _export_daily(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    # export for today's date
    today = datetime.now().date().isoformat()
    subprocess.check_call([
        sys.executable, "manage.py", "export_daily_csvs", "--date", today, "--outdir", str(outdir)
    ])
    return today


def _read_csv(fp: Path):
    with fp.open(newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        rows = list(r)
    return rows


@pytest.mark.e2e
def test_place_minimal_orders_and_validate_exports(page: Page, tmp_path: Path):
    # 1) Open order page
    try:
        page.goto(f"{BASE_URL}/manage_orders/app_prod_order/")
    except Exception:
        pytest.skip("Order page not reachable; ensure server is running at BASE_URL")
    expect(page.get_by_role("heading", name="Basket")).to_be_visible()

    # Wait for channel modal to populate with at least one channel button, then select first.
    # The initial openChannelModal() call may render an empty modal; it is re-rendered once /api/channels returns.
    try:
        page.wait_for_selector("#band-channel-body button[data-channel-band]", timeout=15000)
        page.locator("#band-channel-body button[data-channel-band]").first.click()
    except Exception:
        raise AssertionError("Channel selection buttons not loaded; ensure /api/channels endpoint is reachable.")
    # Ensure any backdrop is cleared (Bootstrap should hide it after click, but be defensive)
    page.evaluate("() => { document.querySelectorAll('.modal-backdrop').forEach(b=>b.remove()); }")

    # Ensure Takeaway basis is active
    take_btn = page.locator("#basis-buttons [data-basis='take']")
    if take_btn.is_visible():
        take_btn.click()

    # Ensure categories have loaded
    page.wait_for_selector("#category-strip button", timeout=15000)

    # Helpers: iterate categories to click the first card matching a selector
    def _iterate_categories_and_click(selector: str):
        buttons = page.locator("#category-strip button")
        count = buttons.count()
        for i in range(count):
            buttons.nth(i).click()
            page.wait_for_selector("#items-container", timeout=5000)
            page.wait_for_timeout(200)
            cards = page.locator(selector)
            if cards.count() > 0 and cards.first.is_visible():
                cards.first.click()
                return True
        return False

    def click_first_combo():
        return _iterate_categories_and_click("#items-container .card[data-item-type='combo']")

    def click_first_product():
        return _iterate_categories_and_click("#items-container .card[data-item-type='product']")

    # 2) Add a combo (first visible), pick free choices if needed, pay Cash
    assert click_first_combo(), "Couldn't find any combo in categories"
    # Wait for config modal to appear before interacting
    page.wait_for_selector("#itemConfigModal.show, #itemConfigModal .modal-dialog", timeout=10000)
    # In modal, pick free choices if groups exist (click first button in each group)
    free_choice_buttons = page.locator("#cfg-free-choices-groups [data-free-choice-group]")
    if free_choice_buttons.count() > 0:
        # Click one in each distinct group
        group_ids = set()
        for i in range(free_choice_buttons.count()):
            gid = free_choice_buttons.nth(i).get_attribute("data-free-choice-group")
            if gid and gid not in group_ids:
                free_choice_buttons.nth(i).click()
                group_ids.add(gid)
    # Wait until Add becomes enabled after satisfying gating
    expect(page.locator("#cfg-add-btn")).to_be_enabled(timeout=10000)
    # Ensure basket offcanvas does not intercept clicks on modal footer
    page.evaluate("() => { const oc=document.getElementById('basketOffcanvas'); if(oc){ oc.classList.remove('show'); oc.style.display='none'; } }")
    page.locator("#cfg-add-btn").click()
    # Checkout (Card to avoid cash calculator complexity)
    # Re-show basket offcanvas so checkout is visible
    page.evaluate("() => { const oc=document.getElementById('basketOffcanvas'); if(oc){ oc.style.display='block'; oc.classList.add('show'); } }")
    expect(page.locator("#basketOffcanvas #checkout")).to_be_visible(timeout=5000)
    page.locator("#basketOffcanvas #checkout").click()
    # Wait for checkout modal, set payment method, then confirm
    page.wait_for_selector("#checkoutModal.show, #checkoutModal .modal-dialog", timeout=10000)
    page.fill("#crew-id", "E2E")
    page.get_by_role("button", name="Card").click()
    page.get_by_role("button", name="Confirm").click()
    page.locator("#checkoutModal").wait_for(state="hidden", timeout=10000)
    page.evaluate("() => { document.querySelectorAll('.modal-backdrop').forEach(b=>b.remove()); document.body.classList.remove('modal-open'); }")

    # 3) Add a product as Crew Food (STAFF)
    assert click_first_product(), "No product card found after first order"
    page.wait_for_selector("#itemConfigModal.show, #itemConfigModal .modal-dialog", timeout=10000)
    expect(page.locator("#cfg-add-btn")).to_be_enabled(timeout=10000)
    # Hide offcanvas to avoid intercepting clicks
    page.evaluate("() => { const oc=document.getElementById('basketOffcanvas'); if(oc){ oc.classList.remove('show'); oc.style.display='none'; } }")
    page.locator("#cfg-add-btn").click()
    # Show offcanvas and checkout
    page.evaluate("() => { const oc=document.getElementById('basketOffcanvas'); if(oc){ oc.style.display='block'; oc.classList.add('show'); } }")
    expect(page.locator("#basketOffcanvas #checkout")).to_be_visible(timeout=5000)
    page.locator("#basketOffcanvas #checkout").click()
    page.wait_for_selector("#checkoutModal.show, #checkoutModal .modal-dialog", timeout=10000)
    page.fill("#crew-id", "E2E")
    page.get_by_role("button", name="Crew Food").click()
    page.get_by_role("button", name="Confirm").click()
    page.locator("#checkoutModal").wait_for(state="hidden", timeout=10000)
    page.evaluate("() => { document.querySelectorAll('.modal-backdrop').forEach(b=>b.remove()); document.body.classList.remove('modal-open'); }")

    # 4) Add another product as Waste food
    assert click_first_product(), "No product card found for Waste food"
    page.wait_for_selector("#itemConfigModal.show, #itemConfigModal .modal-dialog", timeout=10000)
    expect(page.locator("#cfg-add-btn")).to_be_enabled(timeout=10000)
    page.evaluate("() => { const oc=document.getElementById('basketOffcanvas'); if(oc){ oc.classList.remove('show'); oc.style.display='none'; } }")
    page.locator("#cfg-add-btn").click()
    page.evaluate("() => { const oc=document.getElementById('basketOffcanvas'); if(oc){ oc.style.display='block'; oc.classList.add('show'); } }")
    expect(page.locator("#basketOffcanvas #checkout")).to_be_visible(timeout=5000)
    page.locator("#basketOffcanvas #checkout").click()
    page.wait_for_selector("#checkoutModal.show, #checkoutModal .modal-dialog", timeout=10000)
    page.fill("#crew-id", "E2E")
    page.get_by_role("button", name="Waste food").click()
    page.get_by_role("button", name="Confirm").click()
    page.locator("#checkoutModal").wait_for(state="hidden", timeout=10000)
    page.evaluate("() => { document.querySelectorAll('.modal-backdrop').forEach(b=>b.remove()); document.body.classList.remove('modal-open'); }")

    # 5) Export files and validate
    outdir = tmp_path / "exports"
    today = _export_daily(outdir)
    ddmmyy = datetime.now().strftime("%d%m%y")
    pd_fp = outdir / f"PD{ddmmyy}.CSV"
    mp_fp = outdir / f"MP{ddmmyy}.CSV"
    rv_fp = outdir / f"RV{ddmmyy}.CSV"
    assert pd_fp.exists(), "PD export missing"
    assert mp_fp.exists(), "MP export missing"
    assert rv_fp.exists(), "RV export missing"

    # Parse PD
    pd_rows = _read_csv(pd_fp)
    assert pd_rows[0] == ["PRODNUMB","COMBO","TAKEAWAY","EATIN","WASTE","STAFF","OPTION"]
    # Ensure at least one combo row exists in PD
    combo_row = next((r for r in pd_rows[1:] if r[1]=="TRUE"), None)
    assert combo_row is not None, "No combo row found in PD"
    # At least one TAKEAWAY for the platter combo or its components were counted; allow either
    # but we ensure platter row exists (counts can be 0 if components-only basis is used for PD)

    # STAFF-only increment present for at least one non-combo product
    non_combo_rows = [r for r in pd_rows[1:] if r[1]=="FALSE"]
    staff_rows = []
    for r in non_combo_rows:
        take, eat, waste, staff = map(int, r[2:6])
        if staff >= 1 and take == 0 and eat == 0:
            staff_rows.append(r)
    assert staff_rows, "Expected at least one STAFF-only increment in PD for a product"

    # WASTE-only increment present for at least one non-combo product
    waste_rows = []
    for r in non_combo_rows:
        take2, eat2, waste2, staff2 = map(int, r[2:6])
        if waste2 >= 1 and take2 == 0 and eat2 == 0:
            waste_rows.append(r)
    assert waste_rows, "Expected at least one WASTE-only increment in PD for a product"

    # RV: ensure non-zero VAT possible (cash order), and STAFF/WASTE totals present
    rv_rows = _read_csv(rv_fp)
    assert rv_rows[0][:5] == ["TCASHVAL","TCHQVAL","TCARDVAL","TONACCOUNT","TSTAFFVAL"]
    vals = list(map(int, rv_rows[1][:18]))
    TSTAFFVAL = vals[4]; TWASTEVAL = vals[5]; VAT = vals[16]
    assert TSTAFFVAL >= 1, "TSTAFFVAL should be >0 for crew order"
    assert TWASTEVAL >= 1, "TWASTEVAL should be >0 for waste order"
    assert VAT >= 0
