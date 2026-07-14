"""
Test Case 19: View & Cart Brand Products
========================================
The products page has a 'Brands' list in the sidebar. We open the
Polo brand page, verify it, then switch to the H&M brand page.

Note: the brand links show a product count, e.g. "(6) Polo".
get_by_role(name="Polo") still finds it, because by default the
name only needs to CONTAIN the text, not match it exactly.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def test_view_polo_and_hm_brand_products(page: Page):
    # Step 1: open the products page — brands are in the left sidebar
    open_page(page, "/products")
    expect(page.get_by_role("heading", name="Brands")).to_be_visible()

    # Step 2: click the 'Polo' brand link
    page.locator(".brands_products").get_by_role("link", name="Polo").click()

    # Step 3: verify the Polo brand page with its products
    expect(page.locator("h2.title")).to_have_text("Brand - Polo Products")
    expect(page.locator(".productinfo").first).to_be_visible()

    # Step 4: click the 'H&M' brand link
    page.locator(".brands_products").get_by_role("link", name="H&M").click()

    # Step 5: verify the H&M brand page with its products
    expect(page.locator("h2.title")).to_have_text("Brand - H&M Products")
    expect(page.locator(".productinfo").first).to_be_visible()
