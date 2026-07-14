# pages/ — the Page Object Model (POM)
#
# Each file in this folder describes ONE page of the website as a Python
# class: where things are on that page (locators) and what a user can do
# there (methods). Tests and helpers then talk in user language
# ("cart.proceed_to_checkout()") instead of raw selectors.
#
# Why bother? When the site changes, you fix the locator in ONE page
# class instead of in every test that used it. This is the standard
# architecture for UI test suites in the industry.
#
# Importing them from the package directly keeps import lines short:
#     from pages import CartPage

from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage
from pages.payment_page import PaymentPage
