"""
conftest.py
===========
pytest automatically loads this file before running any tests.
Anything defined here is shared by ALL test files.

It contains:
  1. The site address (BASE_URL) and shared test data
  2. An automatic ad blocker (the site's ads make tests fail randomly)
  3. Helper functions for things many tests need to do, like creating
     an account or logging in. Test Case 1 shows the full registration
     flow step by step; the other tests reuse these helpers so they
     can focus on what THEY are testing.

The `page` fixture (a fresh browser tab for each test) is provided
automatically by the pytest-playwright plugin — we don't create it here.
"""

import time

import pytest
import pytest_html.html_report
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Bug fix: always save the HTML report as UTF-8
# ---------------------------------------------------------------------------
# pytest-html 3.x saves report.html using Windows' default text encoding
# (cp1252), which only knows ~250 characters. If a failure message contains
# anything outside that set — like the icon-font characters this site uses —
# saving the report crashes at the very end of the run with
# "UnicodeEncodeError: 'charmap' codec can't encode character".
# The fix: replace the plugin's save method with a copy that writes UTF-8,
# the encoding the report's own <meta charset="utf-8"> header promises.


def _save_report_utf8(self, report_content):
    dir_name = self.logfile.parent
    assets_dir = dir_name / "assets"

    dir_name.mkdir(parents=True, exist_ok=True)
    if not self.self_contained:
        assets_dir.mkdir(parents=True, exist_ok=True)

    self.logfile.write_text(report_content, encoding="utf-8")
    if not self.self_contained:
        (assets_dir / "style.css").write_text(self.style_css, encoding="utf-8")


pytest_html.html_report.HTMLReport._save_report = _save_report_utf8

# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------

# The website we are testing. Every test uses this address.
BASE_URL = "https://automationexercise.com"

# The password we use for every practice account we create.
PASSWORD = "Practice123!"

# The details we type into the registration form.
# Test Case 23 checks that the checkout page shows these exact values,
# which is why we keep them in ONE shared place instead of typing them
# twice (once in the form, once in the check).
ACCOUNT = {
    "name": "Test Student",
    "first_name": "Test",
    "last_name": "Student",
    "company": "QA Practice Inc",
    "address": "123 Automation Street",
    "address2": "Suite 42",
    "country": "United States",
    "state": "California",
    "city": "San Francisco",
    "zipcode": "94101",
    "mobile_number": "5551234567",
}

# This website is only a practice sandbox — no real payment happens.
# We still use an obviously fake card number.
FAKE_CARD = {
    "name_on_card": "Test Student",
    "number": "4242424242424242",
    "cvc": "311",
    "expiry_month": "12",
    "expiry_year": "2030",
}

# The site can be slow sometimes, so give every expect() check
# up to 10 seconds instead of the default 5.
expect.set_options(timeout=10_000)


def unique_email():
    """
    Return a brand-new email address every run, e.g.
    "student.1720855555123@example.com".

    We need this because the site remembers registered emails — if we
    reused the same address, the test would fail on its second run with
    "Email Address already exist!". time.time() is the current time in
    seconds, so the number is different every millisecond.
    """
    return f"student.{int(time.time() * 1000)}@example.com"


# ---------------------------------------------------------------------------
# Ad blocking (runs automatically for every test)
# ---------------------------------------------------------------------------

# The test site shows a lot of ads. Sometimes a full-page ad pops up
# and steals our click, which makes tests fail randomly ("flaky" tests).
# The fix: tell the browser to block requests to ad servers.
AD_KEYWORDS = ["googlesyndication", "doubleclick", "adservice", "googleads"]


@pytest.fixture(autouse=True)
def block_ads(page: Page):
    """
    autouse=True means pytest runs this automatically for EVERY test.

    page.route() lets us inspect each network request the page makes.
    If the request URL contains an ad keyword we abort (block) it,
    otherwise we let it continue normally.
    """
    def handle(route):
        if any(keyword in route.request.url for keyword in AD_KEYWORDS):
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handle)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def open_page(page: Page, path="/"):
    """
    Open a page of the website and dismiss the cookie-consent popup
    if it appears (the site sometimes shows one).

    Example:
        open_page(page)              -> opens the home page
        open_page(page, "/products") -> opens the products page
    """
    page.goto(BASE_URL + path)

    # The consent popup does not always appear, so we only try to
    # close it if the "Consent" button is on screen.
    consent_button = page.get_by_role("button", name="Consent")
    if consent_button.count() > 0 and consent_button.first.is_visible():
        consent_button.first.click()


def add_product_to_cart(page: Page, index=0):
    """
    Add the product at position `index` (0 = first) from a product LIST
    to the cart, then close the "added to cart" popup with the
    'Continue Shopping' button.

    Why the two expect() lines? The popup slides in and out with a short
    animation. If we click while it is still opening — or start the next
    action while it is still closing — the click can miss. Waiting for
    the popup to be fully visible, then fully hidden, makes this rock
    solid. Clicking a half-drawn popup is one of the most common causes
    of "flaky" (randomly failing) tests, and this is how you avoid it.
    """
    modal = page.locator("#cartModal")
    page.locator(".productinfo .add-to-cart").nth(index).click()
    expect(modal).to_be_visible()
    modal.get_by_role("button", name="Continue Shopping").click()
    expect(modal).to_be_hidden()

    # Bootstrap can briefly leave a grey "backdrop" overlay behind after
    # the popup closes. It is invisible-ish but still covers the page, so
    # if we click the next product too soon that overlay swallows the
    # click and no popup appears. Waiting for the backdrop to be removed
    # makes adding several products in a row reliable.
    expect(page.locator(".modal-backdrop")).to_have_count(0)


def go_to_cart(page: Page):
    """
    Open the cart using the top menu bar. We scope the search to
    '.shop-menu' (the menu bar) so we don't accidentally also match the
    hidden 'View Cart' link that lives inside the add-to-cart popup.
    """
    page.locator(".shop-menu").get_by_role("link", name="Cart").click()


def proceed_to_checkout(page: Page):
    """
    Click 'Proceed To Checkout' on the cart page (as a LOGGED-IN user)
    and wait for the checkout page, which shows 'Address Details'.

    Why the retry loop? The 'Proceed To Checkout' button is powered by
    JavaScript, and just after the cart page loads that JavaScript can
    need a moment to wake up. If we click too early, nothing happens. So
    we click, check whether the checkout page appeared, and click again
    if it didn't. This is the same reliable "click-then-check" pattern
    used for the category menu in Test Case 18.
    """
    button = page.get_by_text("Proceed To Checkout")
    address_details = page.get_by_text("Address Details")

    for _ in range(6):
        if button.is_visible():
            button.click()
        try:
            expect(address_details).to_be_visible(timeout=2000)
            return
        except AssertionError:
            continue

    raise AssertionError("The checkout page (Address Details) never appeared")


def create_account(page: Page, email: str):
    """
    Register a new account through the website's signup form and
    finish LOGGED IN as that user.

    Test Case 1 (test_tc01_register_user.py) walks through this exact
    flow step by step with explanations — read that first! Other tests
    call this helper so they don't repeat 20 lines of form-filling.
    """
    open_page(page, "/login")

    # --- Step 1: name + email on the "New User Signup!" form ---
    page.locator('input[data-qa="signup-name"]').fill(ACCOUNT["name"])
    page.locator('input[data-qa="signup-email"]').fill(email)
    page.locator('button[data-qa="signup-button"]').click()

    # --- Step 2: the "Enter Account Information" form ---
    expect(page.get_by_text("Enter Account Information")).to_be_visible()
    page.locator("#id_gender1").check()                      # Title: Mr.
    page.locator('input[data-qa="password"]').fill(PASSWORD)
    page.locator('select[data-qa="days"]').select_option("10")
    page.locator('select[data-qa="months"]').select_option(label="May")
    page.locator('select[data-qa="years"]').select_option("1995")
    page.locator("#newsletter").check()
    page.locator("#optin").check()

    # --- Step 3: address information ---
    page.locator('input[data-qa="first_name"]').fill(ACCOUNT["first_name"])
    page.locator('input[data-qa="last_name"]').fill(ACCOUNT["last_name"])
    page.locator('input[data-qa="company"]').fill(ACCOUNT["company"])
    page.locator('input[data-qa="address"]').fill(ACCOUNT["address"])
    page.locator('input[data-qa="address2"]').fill(ACCOUNT["address2"])
    page.locator('select[data-qa="country"]').select_option(ACCOUNT["country"])
    page.locator('input[data-qa="state"]').fill(ACCOUNT["state"])
    page.locator('input[data-qa="city"]').fill(ACCOUNT["city"])
    page.locator('input[data-qa="zipcode"]').fill(ACCOUNT["zipcode"])
    page.locator('input[data-qa="mobile_number"]').fill(ACCOUNT["mobile_number"])

    # --- Step 4: create the account and continue ---
    page.locator('button[data-qa="create-account"]').click()
    expect(page.get_by_text("Account Created!")).to_be_visible()
    page.locator('a[data-qa="continue-button"]').click()
    expect(page.get_by_text(f"Logged in as {ACCOUNT['name']}")).to_be_visible()


def login(page: Page, email: str, password: str = PASSWORD):
    """Log in through the site's login form."""
    open_page(page, "/login")
    page.locator('input[data-qa="login-email"]').fill(email)
    page.locator('input[data-qa="login-password"]').fill(password)
    page.locator('button[data-qa="login-button"]').click()


def logout(page: Page):
    """Log out using the 'Logout' link in the top menu."""
    page.get_by_role("link", name="Logout").click()


def delete_account(page: Page):
    """
    Delete the currently logged-in account and verify it worked.
    We always clean up the practice accounts we create, so the
    site is not littered with our test data.
    """
    page.get_by_role("link", name="Delete Account").click()
    expect(page.get_by_text("Account Deleted!")).to_be_visible()
    page.locator('a[data-qa="continue-button"]').click()


def pay_and_confirm_order(page: Page):
    """
    Fill the (fake) payment form on the /payment page and confirm
    the order. Used by Test Cases 14, 15, 16 and 24.
    Remember: this is a practice site — no real payment happens.
    """
    page.locator('input[data-qa="name-on-card"]').fill(FAKE_CARD["name_on_card"])
    page.locator('input[data-qa="card-number"]').fill(FAKE_CARD["number"])
    page.locator('input[data-qa="cvc"]').fill(FAKE_CARD["cvc"])
    page.locator('input[data-qa="expiry-month"]').fill(FAKE_CARD["expiry_month"])
    page.locator('input[data-qa="expiry-year"]').fill(FAKE_CARD["expiry_year"])
    page.locator('button[data-qa="pay-button"]').click()

    # The site shows an "Order Placed!" page when it worked.
    expect(page.locator('h2[data-qa="order-placed"]')).to_be_visible()
    expect(
        page.get_by_text("Congratulations! Your order has been confirmed!")
    ).to_be_visible()
