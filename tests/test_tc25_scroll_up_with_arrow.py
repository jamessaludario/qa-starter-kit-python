"""
Test Case 25: Verify Scroll Up using 'Arrow' button
===================================================
The site shows a little orange arrow (bottom-right corner) once you
scroll down. Clicking it should whisk you back to the top.

New ideas in this test:
  - page.keyboard.press("End"): pressing a keyboard key, here the
    'End' key which jumps to the bottom of the page
  - to_be_in_viewport(): checks an element is actually ON SCREEN
    right now (visible in the current scroll position), which is
    exactly what "scrolled to the top" means.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page

# The big slogan at the very top of the home page.
TOP_TEXT = "Full-Fledged practice website for Automation Engineers"


def test_scroll_up_using_arrow_button(page: Page):
    # Step 1: open the home page
    open_page(page)

    # Step 2: scroll all the way DOWN by pressing the 'End' key
    page.keyboard.press("End")

    # Step 3: verify the footer 'SUBSCRIPTION' section is on screen
    expect(page.get_by_role("heading", name="Subscription")).to_be_in_viewport()

    # Step 4: click the orange scroll-up arrow (its id is "scrollUp")
    page.locator("#scrollUp").click()

    # Step 5: verify the top of the page is on screen again
    expect(page.get_by_text(TOP_TEXT).first).to_be_in_viewport()
