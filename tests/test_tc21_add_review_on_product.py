"""
Test Case 21: Add review on product
===================================
Every product details page has a 'Write Your Review' section.
We fill it in, submit, and check the thank-you message.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def test_add_review_on_product(page: Page):
    # Step 1: open the products page and view the first product
    open_page(page, "/products")
    page.get_by_role("link", name="View Product").first.click()

    # Step 2: verify the 'Write Your Review' section is visible
    expect(page.get_by_text("Write Your Review")).to_be_visible()

    # Step 3: fill in name, email and the review text
    page.locator("#name").fill("Test Student")
    page.locator("#email").fill("test-student@example.com")
    page.locator("#review").fill(
        "Great product! (This review was posted by an automated Playwright test.)"
    )

    # Step 4: click the 'Submit' button
    page.locator("#button-review").click()

    # Step 5: verify the thank-you message appears
    expect(page.get_by_text("Thank you for your review.")).to_be_visible()
