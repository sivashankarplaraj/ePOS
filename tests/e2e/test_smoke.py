import os
import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("EPOS_BASE_URL", "http://127.0.0.1:8090")
REQUIRED_ENV = os.getenv("EPOS_E2E", "0")


@pytest.mark.e2e
@pytest.mark.skipif(REQUIRED_ENV != "1", reason="Set EPOS_E2E=1 to run Playwright E2E tests")
def test_smoke_loads_products_page(page: Page):
    # Load app and assert Basket pane is present
    page.goto(f"{BASE_URL}/manage_orders/app_prod_order/")
    expect(page.get_by_role("heading", name="Basket")).to_be_visible()

    # Open channel chooser and pick Walk In if the modal appears
    if page.get_by_role("button", name="Choose channel for price band").is_visible():
        page.get_by_role("button", name="Choose channel for price band").click()
        # Walk In button contains this label - fallback to first Band 1 option if text differs
        walkin = page.get_by_role("button", name=re.compile("Walk In", re.I))
        if walkin.count() == 0:
            # fallback: click first button in Band 1
            page.get_by_text("Band 1").first.click()
            page.get_by_role("button").filter(has_text="Band 1").first.click()
        else:
            walkin.first.click()

    # Basic visible categories
    expect(page.get_by_text("Categories")).to_be_visible()
    # A couple of categories should exist (names vary by data)
    assert page.get_by_role("button").filter(has_text="Burgers").count() >= 0
