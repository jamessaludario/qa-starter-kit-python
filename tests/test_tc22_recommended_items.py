"""
Test Case 22: Add to cart from Recommended items
================================================
The bottom of the home page has a 'Recommended Items' carousel
(a rotating slideshow of products). We add one of them to the cart.

New idea in this test:
  - Carousels only show SOME items at a time. ".item.active" targets
    the slide that is currently visible — clicking a button on a
    hidden slide would fail.
"""

from playwright.sync_api import Page, expect

from conftest import open_page


def test_add_to_cart_from_recommended_items(page: Page):
    # Step 1: open the home page and scroll to the recommended items
    open_page(page)
    recommended = page.locator(".recommended_items")
    recommended.scroll_into_view_if_needed()
    expect(recommended.get_by_role("heading", name="recommended items")).to_be_visible()

    # Step 2: remember the product's name, then add it to the cart.
    # ".item.active" = the carousel slide that is currently shown.
    visible_slide = recommended.locator(".item.active")
    product_name = visible_slide.locator(".productinfo p").first.inner_text()
    print(f"Adding recommended product: {product_name}")
    visible_slide.locator(".add-to-cart").first.click()

    # Step 3: wait for the popup, then click 'View Cart' inside it
    modal = page.locator("#cartModal")
    expect(modal).to_be_visible()
    modal.get_by_role("link", name="View Cart").click()

    # Step 4: verify OUR product is in the cart
    rows = page.locator("#cart_info_table tbody tr")
    expect(rows).to_have_count(1)
    expect(rows.first).to_contain_text(product_name)
