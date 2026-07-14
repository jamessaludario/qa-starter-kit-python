"""
Test Case 8: Verify All Products and product detail page
=========================================================
We open the products page, check the product list is shown, then open
the first product and check its details page shows everything.

New ideas in this test:
  - Combining locators: ".product-information h2" means "the h2 heading
    inside the element with class product-information"
  - to_contain_text() checks that text appears SOMEWHERE inside an element
"""

from playwright.sync_api import Page, expect

from conftest import open_page, BASE_URL


def test_all_products_and_first_product_details(page: Page):
    # Step 1: open the home page and click 'Products'
    open_page(page)
    page.get_by_role("link", name="Products").click()

    # Step 2: verify we are on the ALL PRODUCTS page
    expect(page).to_have_url(BASE_URL + "/products")
    expect(page.get_by_role("heading", name="All Products")).to_be_visible()

    # Step 3: the product list should contain at least one product.
    # ".productinfo" is the CSS class the site uses for each product card.
    products = page.locator(".productinfo")
    expect(products.first).to_be_visible()
    print(f"Number of products on the page: {products.count()}")

    # Step 4: click 'View Product' on the first product
    page.get_by_role("link", name="View Product").first.click()

    # Step 5: the product name should be shown as a heading
    product_name = page.locator(".product-information h2")
    expect(product_name).to_be_visible()
    print(f"Product name: {product_name.inner_text()}")

    # Step 6: all the important details should be visible
    details = page.locator(".product-information")
    expect(details).to_contain_text("Rs.")           # the price
    expect(details).to_contain_text("Category:")
    expect(details).to_contain_text("Availability:")
    expect(details).to_contain_text("Condition:")
    expect(details).to_contain_text("Brand:")
