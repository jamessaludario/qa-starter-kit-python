"""
Test Case 4: Logout User
========================
We log in, then log out, and verify we land back on the login page.

Like Test Case 2, we first create our own throwaway account so the
test does not depend on anything existing beforehand. A test that
prepares everything it needs is called "self-contained" — it can run
on its own, in any order, on any machine.
"""

from playwright.sync_api import Page, expect

from conftest import (
    create_account, login, logout, delete_account, unique_email, ACCOUNT, BASE_URL,
)


def test_logout_returns_to_login_page(page: Page):
    # Preparation: create a fresh account (this leaves us logged in),
    # then log out so we can test the real login -> logout journey.
    email = unique_email()
    create_account(page, email)
    logout(page)

    # Step 1: log in with correct credentials
    login(page, email)
    expect(page.get_by_text(f"Logged in as {ACCOUNT['name']}")).to_be_visible()

    # Step 2: click 'Logout'
    logout(page)

    # Step 3: verify we are back on the login page
    expect(page).to_have_url(BASE_URL + "/login")
    expect(page.get_by_text("Login to your account")).to_be_visible()

    # Cleanup: log back in and delete our throwaway account
    login(page, email)
    delete_account(page)
