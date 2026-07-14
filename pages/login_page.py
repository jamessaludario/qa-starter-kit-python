"""
pages/login_page.py
===================
The /login page — it hosts BOTH forms: "New User Signup!" on one side
and "Login to your account" on the other, plus the multi-step account
registration that follows a signup.
"""

from playwright.sync_api import expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    def login(self, email: str, password: str):
        """Fill the 'Login to your account' form and submit it."""
        self.page.locator('input[data-qa="login-email"]').fill(email)
        self.page.locator('input[data-qa="login-password"]').fill(password)
        self.page.locator('button[data-qa="login-button"]').click()

    def signup(self, name: str, email: str):
        """Fill the 'New User Signup!' form and submit it."""
        self.page.locator('input[data-qa="signup-name"]').fill(name)
        self.page.locator('input[data-qa="signup-email"]').fill(email)
        self.page.locator('button[data-qa="signup-button"]').click()

    def complete_registration(self, password: str, account: dict):
        """
        Fill the "Enter Account Information" form that appears after a
        signup, create the account, and finish LOGGED IN as that user.

        Test Case 1 (test_tc01_register_user.py) walks through this
        exact flow step by step with explanations — read that first!
        """
        # --- The "Enter Account Information" form ---
        expect(self.page.get_by_text("Enter Account Information")).to_be_visible()
        self.page.locator("#id_gender1").check()                # Title: Mr.
        self.page.locator('input[data-qa="password"]').fill(password)
        self.page.locator('select[data-qa="days"]').select_option("10")
        self.page.locator('select[data-qa="months"]').select_option(label="May")
        self.page.locator('select[data-qa="years"]').select_option("1995")
        self.page.locator("#newsletter").check()
        self.page.locator("#optin").check()

        # --- Address information ---
        self.page.locator('input[data-qa="first_name"]').fill(account["first_name"])
        self.page.locator('input[data-qa="last_name"]').fill(account["last_name"])
        self.page.locator('input[data-qa="company"]').fill(account["company"])
        self.page.locator('input[data-qa="address"]').fill(account["address"])
        self.page.locator('input[data-qa="address2"]').fill(account["address2"])
        self.page.locator('select[data-qa="country"]').select_option(account["country"])
        self.page.locator('input[data-qa="state"]').fill(account["state"])
        self.page.locator('input[data-qa="city"]').fill(account["city"])
        self.page.locator('input[data-qa="zipcode"]').fill(account["zipcode"])
        self.page.locator('input[data-qa="mobile_number"]').fill(account["mobile_number"])

        # --- Create the account and continue ---
        self.page.locator('button[data-qa="create-account"]').click()
        expect(self.page.get_by_text("Account Created!")).to_be_visible()
        self.page.locator('a[data-qa="continue-button"]').click()
        expect(
            self.page.get_by_text(f"Logged in as {account['name']}")
        ).to_be_visible()
