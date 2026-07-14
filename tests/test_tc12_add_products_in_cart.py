"""
Test Case 12: Add Products in Cart
==================================
We add TWO different products to the cart and then check the cart
shows both of them, each with quantity 1 and the correct total.

New ideas in this test:
  - add_product_to_cart(): a helper (in conftest.py) that adds a product
    and safely closes the "added to cart" popup. Adding two products is
    as easy as calling it twice.
  - to_have_count()      : checks exactly how many elements match
"""

from playwright.sync_api import Page, expect

from constants import BASE_URL
from helpers.flows import open_page, add_product_to_cart, go_to_cart


def test_add_two_products_to_cart(page: Page):
    # Step 1: open the products page
    open_page(page, "/products")

    # Step 2: add the first two products to the cart.
    # index 0 = first product, index 1 = second (counting starts at 0).
    add_product_to_cart(page, index=0)
    add_product_to_cart(page, index=1)

    # Step 3: open the cart
    go_to_cart(page)

    # Step 4: verify we are on the cart page with exactly 2 products
    expect(page).to_have_url(BASE_URL + "/view_cart")
    rows = page.locator("#cart_info_table tbody tr")
    expect(rows).to_have_count(2)

    # Step 5: verify each product has quantity 1, and that its total
    # equals its price (price x 1 = price).
    for i in range(2):
        row = rows.nth(i)
        expect(row.locator(".cart_quantity")).to_have_text("1")

        price = row.locator(".cart_price").inner_text()    # e.g. "Rs. 500"
        total = row.locator(".cart_total").inner_text()
        print(f"Product {i + 1}: price={price}, total={total}")
        assert price == total, f"Total {total} should equal price {price}"
