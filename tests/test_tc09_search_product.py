"""
Test Case 9: Search Product
===========================
We go to the products page, type "dress" into the search box,
click the search button, and check that results appear.

New ideas in this test:
  - Typing into an input field with .fill()
  - Finding elements by their CSS id, e.g. "#search_product"
    (the "#" means "the element whose id is search_product")
"""

from playwright.sync_api import Page, expect

from conftest import open_page


def test_search_for_a_dress(page: Page):
    # Step 1: go straight to the products page
    open_page(page, "/products")

    # Step 2: type "dress" into the search box
    page.locator("#search_product").fill("dress")

    # Step 3: click the search (magnifying glass) button
    page.locator("#submit_search").click()

    # Step 4: the results section should say "Searched Products"
    expect(page.get_by_role("heading", name="Searched Products")).to_be_visible()

    # Step 5: at least one product should be found
    results = page.locator(".productinfo")
    expect(results.first).to_be_visible()

    # Step 6 (extra check): at least one result name should contain "dress".
    # .all_inner_texts() gives us the text of every product name.
    # Note: we can NOT demand that EVERY name contains "dress", because
    # the site's search also matches product descriptions — a real lesson
    # in testing: always check how a feature actually behaves before
    # writing strict assertions about it!
    names = page.locator(".productinfo p").all_inner_texts()
    print(f"Products found: {names}")
    dresses = [name for name in names if "dress" in name.lower()]
    assert len(dresses) > 0, "Expected at least one product with 'dress' in its name"
