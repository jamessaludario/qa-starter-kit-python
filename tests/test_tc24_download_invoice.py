"""
Test Case 24: Download Invoice after purchase order
===================================================
After placing an order the site offers a 'Download Invoice' button.
We place a full order and verify the invoice file really downloads.

New idea in this test:
  - page.expect_download(): Playwright's way of catching a file
    download. We wrap the click in a `with` block so Playwright is
    already listening BEFORE the download starts.
"""

from playwright.sync_api import Page, expect

from helpers.flows import (
    open_page, add_product_to_cart, go_to_cart, proceed_to_checkout, create_account, pay_and_confirm_order, delete_account,
)
from utils.data import unique_email


def test_download_invoice_after_purchase(page: Page, tmp_path):
    # Step 1: register, add a product, and check out (same journey
    # as Test Case 15 — see that file for the detailed comments)
    create_account(page, unique_email())
    open_page(page, "/products")
    add_product_to_cart(page)
    go_to_cart(page)
    proceed_to_checkout(page)
    page.locator('textarea[name="message"]').fill("Placed by an automated test.")
    page.get_by_role("link", name="Place Order").click()
    pay_and_confirm_order(page)

    # Step 2: click 'Download Invoice' and catch the download
    with page.expect_download() as download_info:
        page.get_by_role("link", name="Download Invoice").click()
    download = download_info.value

    # Step 3: save the file to a temporary folder and verify it
    saved_file = tmp_path / download.suggested_filename
    download.save_as(saved_file)
    print(f"Invoice saved to: {saved_file}")
    assert saved_file.exists(), "The invoice file was not saved!"
    assert saved_file.stat().st_size > 0, "The invoice file is empty!"

    # Step 4: click 'Continue', then cleanup — delete the account
    page.locator('a[data-qa="continue-button"]').click()
    delete_account(page)
