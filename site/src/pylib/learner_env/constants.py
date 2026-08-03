"""constants.py - the same file the kit ships, trimmed to what the
practice shop needs.

It exists so `from constants import BASE_URL` works here exactly as it
does in learn/, and so assertions like

    expect(page).to_have_url(BASE_URL + "/view_cart")

are written the way a real suite writes them.
"""

BASE_URL = "https://automationexercise.com"

PASSWORD = "Practice123!"

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

FAKE_CARD = {
    "name_on_card": "Test Student",
    "number": "4242424242424242",
    "cvc": "311",
    "expiry_month": "12",
    "expiry_year": "2030",
}
