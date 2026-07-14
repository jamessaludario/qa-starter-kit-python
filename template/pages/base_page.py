"""
pages/base_page.py
==================
The parent class all page objects inherit from. Put here whatever EVERY
page of your app has — typically opening by path, plus the shared
navigation (menu bar, sidebar, ...).
"""

from playwright.sync_api import Page

from constants import BASE_URL


class BasePage:
    # Child classes (LoginPage, DashboardPage, ...) override this with
    # the path of "their" page, so page_object.open() knows where to go.
    path = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, path=None):
        """Open this page (or an explicit path) of the app."""
        self.page.goto(BASE_URL + (self.path if path is None else path))
        # If your app shows a cookie-consent popup, dismiss it here so
        # every page object gets that for free. Example:
        #
        # consent = self.page.get_by_role("button", name="Accept")
        # if consent.count() > 0 and consent.first.is_visible():
        #     consent.first.click()
        return self

    # ------------------------------------------------------------------
    # Shared navigation — add methods for whatever appears on every
    # page of YOUR app. Examples:
    #
    # def go_to_dashboard(self):
    #     self.page.get_by_role("link", name="Dashboard").click()
    #
    # def logout(self):
    #     self.page.get_by_role("button", name="Log out").click()
    # ------------------------------------------------------------------
