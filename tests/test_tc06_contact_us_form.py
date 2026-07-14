"""
Test Case 6: Contact Us Form
============================
We fill in the contact form, attach a file, and submit it.

New ideas in this test:
  - tmp_path          : a pytest fixture that gives us an empty temporary
                        folder — perfect for creating a file to upload
  - set_input_files() : how Playwright uploads a file
  - Dialogs           : this form shows a browser popup (an "OK/Cancel"
                        confirm box) when you submit. Playwright dismisses
                        dialogs by default, so we must tell it to press OK.
"""

from playwright.sync_api import Page, expect

from conftest import open_page, BASE_URL


def test_contact_us_form(page: Page, tmp_path):
    # Step 1: open the Contact Us page.
    # We navigate straight to it instead of clicking the menu link,
    # because this practice site sometimes fires a Google ad when you
    # navigate by clicking — and that ad stops the form's JavaScript
    # from loading, so submitting would silently do nothing. Opening the
    # page directly is more reliable for a test. (You'll see the menu
    # link clicked in other tests, like Test Case 7.)
    open_page(page, "/contact_us")

    # Step 2: verify 'GET IN TOUCH' is visible
    expect(page.get_by_role("heading", name="Get In Touch")).to_be_visible()

    # Step 3: fill in name, email, subject and message
    page.locator('input[data-qa="name"]').fill("Test Student")
    page.locator('input[data-qa="email"]').fill("test-student@example.com")
    page.locator('input[data-qa="subject"]').fill("Practicing automation")
    page.locator('textarea[data-qa="message"]').fill(
        "Hello! This message was sent by an automated Playwright test."
    )

    # Step 4: create a small text file and attach it to the form
    upload_file = tmp_path / "hello.txt"
    upload_file.write_text("This file was uploaded by a Playwright test.")
    page.locator('input[name="upload_file"]').set_input_files(upload_file)

    # Step 5: the site shows an 'OK to proceed?' browser popup when we
    # click Submit. We register a handler FIRST that presses OK,
    # otherwise Playwright would automatically press Cancel.
    page.on("dialog", lambda dialog: dialog.accept())
    page.locator('input[data-qa="submit-button"]').click()

    # Step 6: verify the success message.
    # We scope the check to "#contact-page" because the SAME success
    # text also lives in a hidden subscription box in the footer —
    # without scoping, the locator would match 2 elements and fail.
    success = page.locator("#contact-page").get_by_text(
        "Success! Your details have been submitted successfully."
    )
    expect(success).to_be_visible()

    # Step 7: click 'Home' and verify we are back on the home page
    page.locator("#form-section").get_by_role("link", name="Home").click()
    expect(page).to_have_url(BASE_URL + "/")
