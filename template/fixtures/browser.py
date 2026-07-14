"""
fixtures/browser.py
===================
Fixtures that shape how the browser behaves during every test.

(The `page` fixture itself — a fresh browser tab per test — comes from
the pytest-playwright plugin; we only add behavior around it.)
"""

import pytest
from playwright.sync_api import Page, expect

from constants import BLOCKED_URL_KEYWORDS

# Give every expect() check up to 10 seconds instead of the default 5 —
# a good starting point for apps that are sometimes slow. Tune to taste.
expect.set_options(timeout=10_000)


@pytest.fixture(autouse=True)
def block_noisy_requests(page: Page):
    """
    Block requests whose URL matches BLOCKED_URL_KEYWORDS (constants.py),
    for every test automatically. Ads and analytics scripts are a common
    source of flaky tests — popping over the page and stealing clicks.
    With an empty keyword list this does nothing.
    """
    if not BLOCKED_URL_KEYWORDS:
        return

    def handle(route):
        if any(keyword in route.request.url for keyword in BLOCKED_URL_KEYWORDS):
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handle)
