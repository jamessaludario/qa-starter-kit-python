"""
Test Case 23: Verify address details in checkout page
=====================================================
When you registered, you typed in your address. This test checks the
checkout page shows EXACTLY that address back to you — both as the
delivery address and the billing (invoice) address.

This is why conftest.py keeps the account details in one shared
ACCOUNT dictionary: the same data used to FILL the form is used
here to CHECK the result. If we typed it twice, a typo in one place
would make the test lie to us.
"""

from playwright.sync_api import Page, expect

from conftest import (
    open_page, add_product_to_cart, go_to_cart, proceed_to_checkout,
    create_account, delete_account, unique_email, ACCOUNT,
)


def test_checkout_shows_registration_address(page: Page):
    # Step 1: register a new account (address gets saved to the account)
    create_account(page, unique_email())

    # Step 2: add a product to the cart and proceed to checkout
    open_page(page, "/products")
    add_product_to_cart(page)
    go_to_cart(page)
    proceed_to_checkout(page)

    # Step 3: verify the DELIVERY address block shows what we registered
    delivery = page.locator("#address_delivery")
    expect(delivery).to_contain_text(ACCOUNT["first_name"])
    expect(delivery).to_contain_text(ACCOUNT["last_name"])
    expect(delivery).to_contain_text(ACCOUNT["company"])
    expect(delivery).to_contain_text(ACCOUNT["address"])
    expect(delivery).to_contain_text(ACCOUNT["address2"])
    expect(delivery).to_contain_text(ACCOUNT["city"])
    expect(delivery).to_contain_text(ACCOUNT["state"])
    expect(delivery).to_contain_text(ACCOUNT["zipcode"])
    expect(delivery).to_contain_text(ACCOUNT["country"])
    expect(delivery).to_contain_text(ACCOUNT["mobile_number"])

    # Step 4: the BILLING address block should show the same details
    billing = page.locator("#address_invoice")
    expect(billing).to_contain_text(ACCOUNT["address"])
    expect(billing).to_contain_text(ACCOUNT["city"])
    expect(billing).to_contain_text(ACCOUNT["mobile_number"])

    # Step 5: cleanup — delete the account
    delete_account(page)
