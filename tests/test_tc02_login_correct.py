"""
Test Case 2: Login User with correct email and password
=======================================================
We log in with a valid account and verify it works.

The site does not give us a ready-made account, so the test first
creates one itself using the create_account() helper (the full
registration flow is explained in Test Case 1), then logs out so
it can test logging back in.
"""

from playwright.sync_api import Page, expect

from constants import ACCOUNT
from helpers.flows import create_account, login, logout, delete_account
from utils.data import unique_email


def test_login_with_correct_credentials(page: Page):
    # Preparation: create a fresh account, then log out of it
    email = unique_email()
    create_account(page, email)
    logout(page)

    # Step 1: open the login page and verify 'Login to your account'
    page.goto("https://automationexercise.com/login")
    expect(page.get_by_text("Login to your account")).to_be_visible()

    # Step 2: log in with the correct email and password
    login(page, email)

    # Step 3: verify 'Logged in as <username>' appears in the menu
    expect(page.get_by_text(f"Logged in as {ACCOUNT['name']}")).to_be_visible()

    # Step 4: delete the account (cleanup, and part of the official steps)
    delete_account(page)
