"""
Test Case 10: Verify Subscription in home page
==============================================
At the bottom of every page there is a "Subscription" box.
We enter an email address, click the arrow button, and check
that the success message appears.

New idea in this test:
  - scroll_into_view_if_needed(): scrolls the page down so the
    element is on screen (like a human scrolling to the footer)

Note: the site's developers misspelled the input id as
"susbscribe_email" — tests must use the id exactly as it
appears in the page, typos included!
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def test_subscription_on_home_page(page: Page):
    # Step 1: open the home page
    open_page(page)

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
