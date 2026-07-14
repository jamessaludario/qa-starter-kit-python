"""
Test Case 11: Verify Subscription in Cart page
==============================================
Exactly like Test Case 10, but on the cart page instead of the
home page. The footer is the same on every page — this test proves
the subscription box also works when you are looking at your cart.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def test_subscription_on_cart_page(page: Page):
    # Step 1: open the cart page directly
    open_page(page, "/view_cart")

    # Step 2: scroll down to the subscription box in the footer
    email_box = page.locator("#susbscribe_email")
    email_box.scroll_into_view_if_needed()
    expect(page.get_by_role("heading", name="Subscription")).to_be_visible()

    # Step 3: type an email address and click the arrow button
    email_box.fill("test-student@example.com")
    page.locator("#subscribe").click()

    # Step 4: a green success message should appear
    expect(
        page.get_by_text("You have been successfully subscribed!")
    ).to_be_visible()
