"""
Test Case 18: View Category Products
====================================
The left sidebar has categories (Women, Men, Kids) that expand to
show sub-categories. We open Women > Dress, verify the category page,
then switch to Men > Tshirts.

New ideas in this test:
  - Accordion menus: clicking a category header slides its
    sub-categories open (this is a Bootstrap "accordion").
  - Scoping: page.locator("#Women").get_by_role(...) searches only
    inside the element with id "Women". This matters because the word
    "Tshirts" appears under several categories.
  - A small retry helper: right after the page changes, the accordion's
    JavaScript can need a moment before it responds to a click. Instead
    of guessing how long to wait, we click and then CHECK whether the
    sub-category appeared — and click again if it didn't. This is a
    common, reliable pattern for "sometimes-slow" widgets.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def open_subcategory(page: Page, category: str, subcategory: str):
    """
    Expand a sidebar category (e.g. "Women") and click one of its
    sub-categories (e.g. "Dress"). Retries the expand click a few
    times in case the menu's JavaScript isn't ready yet.
    """
    header = page.locator(f'a[href="#{category}"]')
    sub_link = page.locator(f"#{category}").get_by_role("link", name=subcategory)

    for _ in range(5):
        header.click()
        # If the sub-category became visible, the menu opened — click it.
        if sub_link.is_visible():
            sub_link.click()
            return

    # If we get here the menu never opened; fail with a clear message.
    raise AssertionError(f"Could not open {category} > {subcategory}")


def test_view_women_and_men_category_products(page: Page):
    # Step 1: open the home page — categories are in the left sidebar
    open_page(page)
    expect(page.get_by_role("heading", name="Category")).to_be_visible()

    # Step 2: open Women > Dress
    open_subcategory(page, "Women", "Dress")

    # Step 3: verify the category page title
    expect(page.locator("h2.title")).to_contain_text("Women - Dress Products")

    # Step 4: open Men > Tshirts
    open_subcategory(page, "Men", "Tshirts")

    # Step 5: verify we moved to the Men - Tshirts category
    expect(page.locator("h2.title")).to_contain_text("Men - Tshirts Products")
