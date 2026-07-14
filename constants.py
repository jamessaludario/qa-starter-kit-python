"""
constants.py
============
Every fixed value the tests share, in ONE place. If the site address or
the test data ever changes, this is the only file to touch.

Rule of thumb for what belongs here: values that never change while the
tests run. (Things that DO something belong in helpers/ or pages/.)
"""

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

# The test site shows a lot of ads. Requests to these ad servers are
# blocked by the block_ads fixture (see fixtures/browser.py).
AD_KEYWORDS = ["googlesyndication", "doubleclick", "adservice", "googleads"]
