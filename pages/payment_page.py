"""
pages/payment_page.py
=====================
The /payment page — the (fake) card form shown at the end of checkout.
Remember: this is a practice site, no real payment happens.
"""

from playwright.sync_api import expect

from pages.base_page import BasePage


class PaymentPage(BasePage):
    path = "/payment"

    def pay_and_confirm(self, card: dict):
        """Fill the card form, confirm the order, and verify it worked."""
        self.page.locator('input[data-qa="name-on-card"]').fill(card["name_on_card"])
        self.page.locator('input[data-qa="card-number"]').fill(card["number"])
        self.page.locator('input[data-qa="cvc"]').fill(card["cvc"])
        self.page.locator('input[data-qa="expiry-month"]').fill(card["expiry_month"])
        self.page.locator('input[data-qa="expiry-year"]').fill(card["expiry_year"])
        self.page.locator('button[data-qa="pay-button"]').click()

        # The site shows an "Order Placed!" page when it worked.
        expect(self.page.locator('h2[data-qa="order-placed"]')).to_be_visible()
        expect(
            self.page.get_by_text("Congratulations! Your order has been confirmed!")
        ).to_be_visible()
