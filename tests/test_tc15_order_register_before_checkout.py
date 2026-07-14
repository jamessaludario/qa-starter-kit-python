"""
Test Case 15: Place Order — Register before Checkout
====================================================
Same shopping journey as Test Case 14, but in a different order:
this time we register FIRST, and only then shop and check out.

Testing the same feature through different paths is important:
users don't all do things in the same order, and bugs often hide
in the less common paths.
"""

from playwright.sync_api import Page, expect

from helpers.flows import (
    open_page, add_product_to_cart, go_to_cart, proceed_to_checkout, create_account, pay_and_confirm_order, delete_account,
)
from utils.data import unique_email


def test_place_order_register_before_checkout(page: Page):
    # Step 1: register a new account first (helper — see Test Case 1)
    create_account(page, unique_email())

    # Step 2: now shop — add the first product and view the cart
    open_page(page, "/products")
    add_product_to_cart(page)
    go_to_cart(page)

    # Step 3: proceed to checkout. We are already logged in, so no
    # popup appears this time — we go straight to the checkout page.
    proceed_to_checkout(page)
    expect(page.get_by_text("Review Your Order")).to_be_visible()

    # Step 4: write an order comment and place the order
    page.locator('textarea[name="message"]').fill("Placed by an automated test.")
    page.get_by_role("link", name="Place Order").click()

    # Step 5: pay with the fake card and verify the order is confirmed
    pay_and_confirm_order(page)

    # Step 6: cleanup — delete the account we created
    delete_account(page)
