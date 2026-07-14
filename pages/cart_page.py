"""
pages/cart_page.py
==================
The /view_cart page — the shopping cart.
"""

from playwright.sync_api import expect

from pages.base_page import BasePage


class CartPage(BasePage):
    path = "/view_cart"

    def proceed_to_checkout(self):
        """
        Click 'Proceed To Checkout' (as a LOGGED-IN user) and wait for
        the checkout page, which shows 'Address Details'.

        Why the retry loop? The 'Proceed To Checkout' button is powered
        by JavaScript, and just after the cart page loads that
        JavaScript can need a moment to wake up. If we click too early,
        nothing happens. So we click, check whether the checkout page
        appeared, and click again if it didn't. This is the same
        reliable "click-then-check" pattern used for the category menu
        in Test Case 18.
        """
        button = self.page.get_by_text("Proceed To Checkout")
        address_details = self.page.get_by_text("Address Details")

        for _ in range(6):
            if button.is_visible():
                button.click()
            try:
                expect(address_details).to_be_visible(timeout=2000)
                return
            except AssertionError:
                continue

        raise AssertionError("The checkout page (Address Details) never appeared")
