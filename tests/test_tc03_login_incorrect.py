"""
Test Case 3: Login User with incorrect email and password
=========================================================
Good tests don't only check that things WORK — they also check that
the site handles mistakes correctly. Here we try to log in with an
account that does not exist and expect a friendly error message.

New idea in this test:
  - Selecting inputs by attribute: input[data-qa="login-email"] means
    "the input whose data-qa attribute equals login-email".
    Attributes like data-qa are added by developers specifically
    to make testing easier.
"""

from playwright.sync_api import Page, expect

from conftest import open_page


def test_login_with_wrong_password_shows_error(page: Page):
    # Step 1: open the login page
    open_page(page, "/login")

    # Step 2: verify 'Login to your account' is visible
    expect(page.get_by_text("Login to your account")).to_be_visible()

    # Step 3: fill in an email and password that do not exist
    page.locator('input[data-qa="login-email"]').fill("not-a-real-user@example.com")
    page.locator('input[data-qa="login-password"]').fill("wrong-password-123")

    # Step 4: click the Login button
    page.locator('button[data-qa="login-button"]').click()

    # Step 5: the site should show an error message
    expect(page.get_by_text("Your email or password is incorrect!")).to_be_visible()
