"""
desktop/fixtures/calculator.py
================================
The `calculator` fixture: the desktop-track equivalent of the `page`
fixture pytest-playwright gives the web track. It launches a fresh
Calculator before each test and guarantees it's closed afterwards, so
tests never manage the app's lifecycle themselves.
"""

import pytest

from desktop.pages.calculator_page import CalculatorPage


@pytest.fixture
def calculator():
    app = CalculatorPage()
    try:
        app.open()
        yield app
    finally:
        # try/finally, NOT just a line after `yield`: if open() itself
        # fails, the code after a yield never runs, so the half-started
        # app would be left on screen. Six failing runs like that leave a
        # dozen Calculators open - and then even correct code breaks,
        # because "the window titled Calculator" is suddenly ambiguous.
        app.close()
