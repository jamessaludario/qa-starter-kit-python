"""
pages/products_page.py
======================
The /products page — the product list, and anywhere else a product grid
appears (the home page uses the same layout, so this class works there
too).
"""

from playwright.sync_api import expect

from pages.base_page import BasePage


class ProductsPage(BasePage):
    path = "/products"

    def add_product_to_cart(self, index=0):
        """
        Add the product at position `index` (0 = first) from a product
        LIST to the cart, then close the "added to cart" popup with the
        'Continue Shopping' button.

        Why the two expect() lines? The popup slides in and out with a
        short animation. If we click while it is still opening — or
        start the next action while it is still closing — the click can
        miss. Waiting for the popup to be fully visible, then fully
        hidden, makes this rock solid. Clicking a half-drawn popup is
        one of the most common causes of "flaky" (randomly failing)
        tests, and this is how you avoid it.
        """
        modal = self.page.locator("#cartModal")
        self.page.locator(".productinfo .add-to-cart").nth(index).click()
        expect(modal).to_be_visible()
        modal.get_by_role("button", name="Continue Shopping").click()
        expect(modal).to_be_hidden()

        # Bootstrap can briefly leave a grey "backdrop" overlay behind
        # after the popup closes. It is invisible-ish but still covers
        # the page, so if we click the next product too soon that
        # overlay swallows the click and no popup appears. Waiting for
        # the backdrop to be removed makes adding several products in a
        # row reliable.
        expect(self.page.locator(".modal-backdrop")).to_have_count(0)
