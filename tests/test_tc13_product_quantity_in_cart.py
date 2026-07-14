"""
Test Case 13: Verify Product quantity in Cart
=============================================
On a product's details page you can choose HOW MANY you want.
We set the quantity to 4, add to cart, and verify the cart really
shows quantity 4.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def test_cart_shows_chosen_quantity(page: Page):
    # Step 1: open the home page and view the first product's details
    open_page(page)
    page.get_by_role("link", name="View Product").first.click()

    # Step 2: verify we are on the product details page
    expect(page.locator(".product-information h2")).to_be_visible()

    # Step 3: change the quantity from 1 to 4.
    # .fill() clears the field first, then types the new value.
    page.locator("#quantity").fill("4")

    # Step 4: click the 'Add to cart' button
    page.get_by_role("button", name="Add to cart").click()

    # Step 5: wait for the popup to fully appear, then click 'View Cart'.
    # We wait for the popup first so we never click while it is still
    # sliding into view (a common cause of randomly failing tests).
    modal = page.locator("#cartModal")
    expect(modal).to_be_visible()
    modal.get_by_role("link", name="View Cart").click()

    # Step 6: the cart should show our product with quantity 4
    rows = page.locator("#cart_info_table tbody tr")
    expect(rows).to_have_count(1)
    expect(rows.first.locator(".cart_quantity")).to_have_text("4")
