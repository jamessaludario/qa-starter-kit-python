"""
Test Case 7: Verify Test Cases Page
===================================
The simplest test in the suite: click the 'Test Cases' menu link and
check that the test cases page opens. (Fun fact: that page is where
this whole test suite comes from!)
"""

from playwright.sync_api import Page, expect

from conftest import open_page, BASE_URL


def test_test_cases_page_opens(page: Page):
    # Step 1: open the home page
    open_page(page)

    # Step 2: click the 'Test Cases' link in the menu.
    # .first because the page contains more than one 'Test Cases' link
    # (one in the menu, one big button lower on the page).
    page.get_by_role("link", name="Test Cases").first.click()

    # Step 3: verify we landed on the test cases page
    expect(page).to_have_url(BASE_URL + "/test_cases")
    expect(page.get_by_text("Below is the list of test Cases")).to_be_visible()
