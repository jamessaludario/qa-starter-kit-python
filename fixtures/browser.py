"""
fixtures/browser.py
===================
Fixtures that shape how the browser behaves during every test.

(The `page` fixture itself — a fresh browser tab per test — comes from
the pytest-playwright plugin; we only add behavior around it.)
"""

import pytest
from playwright.sync_api import Page, expect

from constants import AD_KEYWORDS

# The site can be slow sometimes, so give every expect() check
# up to 10 seconds instead of the default 5.
expect.set_options(timeout=10_000)


@pytest.fixture(autouse=True)
def block_ads(page: Page):
    """
    Block requests to ad servers, for every test automatically.

    The test site shows a lot of ads. Sometimes a full-page ad pops up
    and steals our click, which makes tests fail randomly ("flaky"
    tests). page.route() lets us inspect each network request the page
    makes: if the URL contains an ad keyword we abort (block) it,
    otherwise we let it continue normally.
    """
    def handle(route):
        if any(keyword in route.request.url for keyword in AD_KEYWORDS):
            route.abort()
        else:
            route.continue_()

    page.route("**/*", handle)
