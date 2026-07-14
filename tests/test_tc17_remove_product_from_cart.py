"""
Test Case 17: Remove Products From Cart
=======================================
We add a product to the cart, then click the little 'X' button to
remove it, and verify the cart becomes empty.

New idea in this test:
  - to_have_count(0): a locator matching ZERO elements is how we
    check that something is GONE from the page.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page, add_product_to_cart, go_to_cart


def test_remove_product_from_cart(page: Page):
    # Step 1: add the first product to the cart and open the cart
    open_page(page, "/products")
    add_product_to_cart(page)
    go_to_cart(page)

    # Step 2: the cart should have exactly 1 product
    rows = page.locator("#cart_info_table tbody tr")
    expect(rows).to_have_count(1)

    # Step 3: click the 'X' button to remove the product
    page.locator(".cart_quantity_delete").click()

    # Step 4: the row disappears and the cart says it is empty
    expect(rows).to_have_count(0)
    expect(page.get_by_text("Cart is empty!")).to_be_visible()
