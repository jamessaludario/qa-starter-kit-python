"""
Test Case 5: Register User with existing email
==============================================
The site must NOT allow two accounts with the same email address.
We create an account, log out, then try to sign up AGAIN with the
same email — and expect an error message.
"""

from playwright.sync_api import Page, expect

from constants import ACCOUNT
from helpers.flows import (
    create_account, login, logout, delete_account, open_page,
)
from utils.data import unique_email


def test_register_with_existing_email_shows_error(page: Page):
    # Preparation: create an account so the email is "taken", then log out
    email = unique_email()
    create_account(page, email)
    logout(page)

    # Step 1: open the signup page and verify 'New User Signup!'
    open_page(page, "/login")
    expect(page.get_by_text("New User Signup!")).to_be_visible()

    # Step 2: try to sign up with the SAME email again
    page.locator('input[data-qa="signup-name"]').fill(ACCOUNT["name"])
    page.locator('input[data-qa="signup-email"]').fill(email)
    page.locator('button[data-qa="signup-button"]').click()

    # Step 3: the site should refuse with an error message
    expect(page.get_by_text("Email Address already exist!")).to_be_visible()

    # Cleanup: log in and delete our throwaway account
    login(page, email)
    delete_account(page)
