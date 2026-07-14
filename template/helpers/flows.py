"""
helpers/flows.py
================
User JOURNEYS — actions that many tests need, like "log in" or "create
a record and open it". Tests call these so they can focus on the one
thing THEY are testing.

The layering to keep in mind:

    test  ->  helpers/flows.py  ->  pages/  ->  the browser
    (WHAT to verify)  (the journey)  (WHERE things are)

Helpers should not contain locators — that knowledge belongs in the
page objects. Example of the pattern:

    from constants import TEST_USER
    from pages import LoginPage

    def login(page: Page):
        login_page = LoginPage(page)
        login_page.open()
        login_page.login(TEST_USER["email"], TEST_USER["password"])
"""

from playwright.sync_api import Page

from pages import BasePage


def open_app(page: Page, path="/"):
    """Open a page of the app (BASE_URL + path)."""
    BasePage(page).open(path)
