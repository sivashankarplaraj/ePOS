import sys
import time
import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8090"

@pytest.mark.e2e
def test_category_strip_no_flicker_and_single_row():
    # Small viewport like a phone
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 375, "height": 700})
        page = context.new_page()
        page.goto(f"{BASE_URL}/manage_orders/app_prod_order/", wait_until="networkidle")

        # Choose a channel from the modal so categories can load
        page.wait_for_selector("#bandChannelModal [data-channel-band]")
        # Click the first available channel; force in case backdrop layers intercept pointer
        page.locator("#bandChannelModal [data-channel-band]").first.click(force=True)
        # Wait for category strip to populate
        page.wait_for_selector("#category-strip .btn")

        # Ensure the strip uses nowrap and is horizontally scrollable
        flex_wrap = page.evaluate("""
            () => getComputedStyle(document.querySelector('#category-strip')).flexWrap
        """)
        assert flex_wrap.lower() == 'nowrap'

        # Capture initial height
        initial_height = page.evaluate("""
            () => document.querySelector('#category-strip').getBoundingClientRect().height
        """)

        # Click through first few categories and ensure height remains stable
        buttons = page.query_selector_all("#category-strip .btn")
        # Limit to first 6 to keep runtime tight
        for i, btn in enumerate(buttons[:6]):
            btn.click()
            # Give the UI a short moment to update items and re-render categories
            page.wait_for_timeout(150)
            new_height = page.evaluate("""
                () => document.querySelector('#category-strip').getBoundingClientRect().height
            """)
            # Height can fluctuate by sub-pixel; allow small tolerance
            assert abs(new_height - initial_height) < 2.0, f"Category strip height changed from {initial_height} to {new_height} after click {i}"

        # Additionally ensure buttons are in a single row by checking unique offsetTop
        unique_tops = page.evaluate("""
            () => Array.from(document.querySelectorAll('#category-strip .btn')).map(b=>b.offsetTop).reduce((s,v)=>{ if(!s.includes(v)) s.push(v); return s; }, [])
        """)
        assert len(unique_tops) == 1, f"Buttons wrapped into multiple rows: tops={unique_tops}"

        context.close()
        browser.close()
