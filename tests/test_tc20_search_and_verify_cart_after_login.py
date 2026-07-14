"""
Test Case 20: Search Products and Verify Cart After Login
=========================================================
A clever test: we search for products as a GUEST, add them all to
the cart, then LOG IN — and check the cart kept our products.
(Websites often lose the guest cart on login; this verifies the
site does it right.)

New idea in this test:
  - A for-loop: we call add_product_to_cart() once for each search
    result to add them all, one by one.
"""

from playwright.sync_api import Page, expect

from conftest import (
    open_page, add_product_to_cart, go_to_cart,
    create_account, login, logout, delete_account, unique_email,
)


def test_cart_is_kept_after_login(page: Page):
    # Preparation: create an account to log in with later, then log out
    email = unique_email()
    create_account(page, email)
    logout(page)

    # Step 1: search for "jeans" on the products page
    open_page(page, "/products")
    page.locator("#search_product").fill("jeans")
    page.locator("#submit_search").click()
    expect(page.get_by_role("heading", name="Searched Products")).to_be_visible()

    # Step 2: add EVERY search result to the cart.
    # add_product_to_cart() (in conftest.py) adds one product and safely
    # closes the popup, so we just call it once per search result.
    number_of_products = page.locator(".productinfo .add-to-cart").count()
    print(f"Adding {number_of_products} products to the cart")
    for i in range(number_of_products):
        add_product_to_cart(page, index=i)

    # Step 3: open the cart and verify all products are there
    go_to_cart(page)
    rows = page.locator("#cart_info_table tbody tr")
    expect(rows).to_have_count(number_of_products)

    # Step 4: now log in...
    login(page, email)

    # Step 5: ...open the cart again and verify NOTHING was lost
    go_to_cart(page)
    expect(rows).to_have_count(number_of_products)

    # Cleanup: delete the account
    delete_account(page)
