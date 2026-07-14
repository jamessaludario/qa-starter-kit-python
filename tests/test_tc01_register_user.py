"""
Test Case 1: Register User
==========================
The full "sign up for a new account" journey, written out step by step.
This is the longest test in the suite because it teaches the whole flow —
other tests reuse the create_account() helper from conftest.py instead
of repeating all of this.

New ideas in this test:
  - .check()        : tick a radio button or checkbox
  - .select_option(): choose a value from a dropdown (<select>)
  - unique_email()  : we generate a NEW email every run, because the
                      site refuses emails that are already registered
"""

from playwright.sync_api import Page, expect

from conftest import open_page, unique_email, ACCOUNT, PASSWORD


def test_register_user(page: Page):
    # Step 1-2: open the home page and verify it loaded
    open_page(page)
    expect(page).to_have_title("Automation Exercise")

    # Step 3: click 'Signup / Login'
    page.get_by_role("link", name="Signup / Login").click()

    # Step 4: verify 'New User Signup!' is visible
    expect(page.get_by_text("New User Signup!")).to_be_visible()

    # Step 5: enter a name and a brand-new email address
    email = unique_email()
    page.locator('input[data-qa="signup-name"]').fill(ACCOUNT["name"])
    page.locator('input[data-qa="signup-email"]').fill(email)

    # Step 6: click the 'Signup' button
    page.locator('button[data-qa="signup-button"]').click()

    # Step 7: verify 'ENTER ACCOUNT INFORMATION' is visible
    expect(page.get_by_text("Enter Account Information")).to_be_visible()

    # Step 8: fill in title, password and date of birth
    page.locator("#id_gender1").check()                       # Title: Mr.
    page.locator('input[data-qa="password"]').fill(PASSWORD)
    page.locator('select[data-qa="days"]').select_option("10")
    page.locator('select[data-qa="months"]').select_option(label="May")
    page.locator('select[data-qa="years"]').select_option("1995")

    # Steps 9-10: tick the newsletter and offers checkboxes
    page.locator("#newsletter").check()
    page.locator("#optin").check()

    # Step 11: fill in the address details (shared data from conftest.py)
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

    # Step 12: click 'Create Account'
    page.locator('button[data-qa="create-account"]').click()

    # Step 13-14: verify 'ACCOUNT CREATED!' and click 'Continue'
    expect(page.get_by_text("Account Created!")).to_be_visible()
    page.locator('a[data-qa="continue-button"]').click()

    # Step 15: verify we are logged in as our new user
    expect(page.get_by_text(f"Logged in as {ACCOUNT['name']}")).to_be_visible()

    # Step 16-17: delete the account and verify 'ACCOUNT DELETED!'
    page.get_by_role("link", name="Delete Account").click()
    expect(page.get_by_text("Account Deleted!")).to_be_visible()
    page.locator('a[data-qa="continue-button"]').click()
