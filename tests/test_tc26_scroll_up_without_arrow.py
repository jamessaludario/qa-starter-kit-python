"""
Test Case 26: Verify Scroll Up without 'Arrow' button
=====================================================
Same as Test Case 25, but instead of clicking the arrow button we
scroll back up "by hand".

New idea in this test:
  - page.evaluate(): runs a line of JavaScript inside the page.
    window.scrollTo(0, 0) is JavaScript for "scroll to the top".
    Playwright can do almost everything without JavaScript, but
    it's good to know this escape hatch exists.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page

# The big slogan at the very top of the home page.
TOP_TEXT = "Full-Fledged practice website for Automation Engineers"


def test_scroll_up_without_arrow_button(page: Page):
    # Step 1: open the home page
    open_page(page)

    # Step 2: scroll all the way DOWN by pressing the 'End' key
    page.keyboard.press("End")

    # Step 3: verify the footer 'SUBSCRIPTION' section is on screen
    expect(page.get_by_role("heading", name="Subscription")).to_be_in_viewport()

    # Step 4: scroll back UP with a line of JavaScript (no arrow button)
    page.evaluate("window.scrollTo(0, 0)")

    # Step 5: verify the top of the page is on screen again
    expect(page.get_by_text(TOP_TEXT).first).to_be_in_viewport()
