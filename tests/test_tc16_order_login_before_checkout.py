"""
Test Case 16: Place Order — Login before Checkout
=================================================
The third checkout path: an EXISTING user logs in first, then shops
and places an order. (We create the "existing" account ourselves at
the start, then log out, so the test is self-contained.)
"""

from playwright.sync_api import Page, expect

from conftest import (
    open_page, add_product_to_cart, go_to_cart, proceed_to_checkout,
    create_account, login, logout,
    pay_and_confirm_order, delete_account, unique_email, ACCOUNT,
)


def test_place_order_login_before_checkout(page: Page):
    # Preparation: create an account and log out again
    email = unique_email()
    create_account(page, email)
    logout(page)

    # Step 1: log in with our existing account
    login(page, email)
    expect(page.get_by_text(f"Logged in as {ACCOUNT['name']}")).to_be_visible()

    # Step 2: add the first product to the cart and view the cart
    open_page(page, "/products")
    add_product_to_cart(page)
    go_to_cart(page)

    # Step 3: proceed to checkout — logged in, so straight through
    proceed_to_checkout(page)
    expect(page.get_by_text("Review Your Order")).to_be_visible()

    # Step 4: write an order comment and place the order
    page.locator('textarea[name="message"]').fill("Placed by an automated test.")
    page.get_by_role("link", name="Place Order").click()

    # Step 5: pay with the fake card and verify the order is confirmed
    pay_and_confirm_order(page)

    # Step 6: cleanup — delete the account
    delete_account(page)
