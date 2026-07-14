"""
conftest.py
===========
pytest automatically loads this file before running any tests. Ours is
deliberately tiny: it just plugs in the project's building blocks, which
each live in their own folder so you always know where to look:

    constants.py     your app's URL (from .env) and shared test data
    pages/           page objects — one class per page of YOUR app
    helpers/         user journeys (login, ...) built from page objects
    fixtures/        things pytest runs around every test
    utils/           small standalone tools like unique_email()

The `page` fixture (a fresh browser tab for each test) is provided
automatically by the pytest-playwright plugin — we don't create it here.
"""

pytest_plugins = [
    "fixtures.browser",
    "fixtures.reporting",
]
