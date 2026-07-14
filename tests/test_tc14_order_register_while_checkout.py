"""
Test Case 14: Place Order — Register while Checkout
===================================================
A full shopping journey: add a product as a guest, start checkout,
get asked to register, create the account MID-CHECKOUT, then finish
the order and pay (with a fake card — this is a practice site,
no real payment happens).

This test reuses three helpers from conftest.py:
  create_account()        - the registration flow (explained in TC 1)
  pay_and_confirm_order() - fills the fake payment form
  delete_account()        - cleanup at the end
"""

from playwright.sync_api import Page, expect

from conftest import (
    open_page, add_product_to_cart, go_to_cart, proceed_to_checkout,
    create_account, pay_and_confirm_order, delete_account, unique_email,
)


def test_place_order_register_while_checkout(page: Page):
    # Step 1: add the first product to the cart and view the cart
    open_page(page, "/products")
    add_product_to_cart(page)
    go_to_cart(page)

    # Step 2: click 'Proceed To Checkout'. Because we are NOT logged in,
    # a popup asks us to register or login. We click a few times if
    # needed, because the button's JavaScript can be slow to wake up
    # right after the cart page loads (see proceed_to_checkout() in
    # conftest.py for the same idea).
    register_link = page.get_by_role("link", name="Register / Login")
    checkout_button = page.get_by_text("Proceed To Checkout")
    for _ in range(6):
        if checkout_button.is_visible():
            checkout_button.click()
        if register_link.is_visible():
            break
    register_link.click()

    # Step 3: register a new account (helper — see Test Case 1)
    create_account(page, unique_email())

    # Step 4: our cart survived registration! Open it and check out.
    go_to_cart(page)
    proceed_to_checkout(page)

    # Step 5: verify the checkout page shows address and order review
    expect(page.get_by_text("Review Your Order")).to_be_visible()

    # Step 6: write an order comment and place the order
    page.locator('textarea[name="message"]').fill("Placed by an automated test.")
    page.get_by_role("link", name="Place Order").click()

    # Step 7: pay with the fake card and verify the order is confirmed
    pay_and_confirm_order(page)

    # Step 8: cleanup — delete the account we created
    delete_account(page)
