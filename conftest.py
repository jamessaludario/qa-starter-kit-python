"""
conftest.py
===========
pytest automatically loads this file before running any tests. Ours is
deliberately tiny: it just plugs in the kit's building blocks, which
each live in their own folder so you always know where to look:

    constants.py     shared data: the site address, account details, ...
    pages/           page objects — one class per page of the website
                     (WHERE things are and what a user can do there)
    helpers/         user journeys like create_account(), built from
                     page objects (tests call these)
    fixtures/        things pytest runs around every test: the ad
                     blocker, failure screenshots, report labels
    utils/           small standalone tools like unique_email()

The `page` fixture (a fresh browser tab for each test) is provided
automatically by the pytest-playwright plugin — we don't create it here.
"""

# Load our fixture modules. Listing them here has the same effect as if
# their contents were written directly in this file.
pytest_plugins = [
    "fixtures.browser",
    "fixtures.reporting",
]
