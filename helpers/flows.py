"""
helpers/flows.py
================
User JOURNEYS — actions that many tests need, like "create an account"
or "add a product and open the cart". Tests call these so they can
focus on the one thing THEY are testing.

Notice the layering: these helpers don't contain a single locator.
They combine methods from the page objects (pages/ folder), which is
where all the "how do I find that button" knowledge lives:

    test  ->  helpers/flows.py  ->  pages/  ->  the browser
    (WHAT to verify)  (the journey)  (WHERE things are)
"""

from playwright.sync_api import Page

from constants import ACCOUNT, FAKE_CARD, PASSWORD
from pages import BasePage, CartPage, LoginPage, PaymentPage, ProductsPage


def open_page(page: Page, path="/"):
    """
    Open a page of the website (and dismiss the cookie popup if it
    appears).

    Example:
        open_page(page)              -> opens the home page
        open_page(page, "/products") -> opens the products page
    """
    BasePage(page).open(path)


def add_product_to_cart(page: Page, index=0):
    """
    Add the product at position `index` (0 = first) from a product LIST
    to the cart, then close the "added to cart" popup. Works on any page
    that shows a product grid (home, /products, search results...).
    """
    ProductsPage(page).add_product_to_cart(index)


def go_to_cart(page: Page):
    """Open the cart using the top menu bar."""
    BasePage(page).go_to_cart()


def proceed_to_checkout(page: Page):
    """From the cart, click through to the checkout page (logged in)."""
    CartPage(page).proceed_to_checkout()


def create_account(page: Page, email: str):
    """
    Register a new account through the website's signup form and
    finish LOGGED IN as that user.

    Test Case 1 (test_tc01_register_user.py) walks through this exact
    flow step by step with explanations — read that first! Other tests
    call this helper so they don't repeat 20 lines of form-filling.
    """
    login_page = LoginPage(page)
    login_page.open()
    login_page.signup(ACCOUNT["name"], email)
    login_page.complete_registration(PASSWORD, ACCOUNT)


def login(page: Page, email: str, password: str = PASSWORD):
    """Log in through the site's login form."""
    login_page = LoginPage(page)
    login_page.open()
    login_page.login(email, password)


def logout(page: Page):
    """Log out using the 'Logout' link in the top menu."""
    BasePage(page).logout()


def delete_account(page: Page):
    """Delete the currently logged-in account and verify it worked."""
    BasePage(page).delete_account()


def pay_and_confirm_order(page: Page):
    """
    Fill the (fake) payment form on the /payment page and confirm
    the order. Used by Test Cases 14, 15, 16 and 24.
    """
    PaymentPage(page).pay_and_confirm(FAKE_CARD)
