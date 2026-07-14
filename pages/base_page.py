"""
pages/base_page.py
==================
The parent class all page objects inherit from. It holds what EVERY page
of this site has: the address bar (open a path) and the top menu bar
(cart, logout, delete account, ...).
"""

from playwright.sync_api import Page, expect

from constants import BASE_URL


class BasePage:
    # Child classes (LoginPage, CartPage, ...) override this with the
    # path of "their" page, so page_object.open() knows where to go.
    path = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, path=None):
        """
        Open this page (or an explicit path) and dismiss the site's
        cookie-consent popup if it appears.
        """
        self.page.goto(BASE_URL + (self.path if path is None else path))

        # The consent popup does not always appear, so we only try to
        # close it if the "Consent" button is on screen.
        consent_button = self.page.get_by_role("button", name="Consent")
        if consent_button.count() > 0 and consent_button.first.is_visible():
            consent_button.first.click()
        return self

    # ------------------------------------------------------------------
    # The top menu bar (present on every page)
    # ------------------------------------------------------------------

    def go_to_cart(self):
        """
        Open the cart using the top menu bar. We scope the search to
        '.shop-menu' (the menu bar) so we don't accidentally also match
        the hidden 'View Cart' link inside the add-to-cart popup.
        """
        self.page.locator(".shop-menu").get_by_role("link", name="Cart").click()

    def logout(self):
        """Log out using the 'Logout' link in the top menu."""
        self.page.get_by_role("link", name="Logout").click()

    def delete_account(self):
        """
        Delete the currently logged-in account and verify it worked.
        We always clean up the practice accounts we create, so the
        site is not littered with our test data.
        """
        self.page.get_by_role("link", name="Delete Account").click()
        expect(self.page.get_by_text("Account Deleted!")).to_be_visible()
        self.page.locator('a[data-qa="continue-button"]').click()
