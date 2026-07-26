"""
desktop/pages/calculator_page.py
=================================
Windows Calculator - the ONE place that knows how to find its buttons
and read its result display.

Desktop apps have no data-qa attributes, but UI Automation gives every
control TWO possible addresses, and the choice matters:

  - its NAME, the label a screen reader reads out ("One", "Plus")
  - its AUTOMATION ID, an internal name the developer set ("num1Button")

We use automation ids here. Names are TRANSLATED, so a test written
against "Plus" fails the moment it runs on a Spanish or Japanese
Windows, while num1Button is the same everywhere. Automation ids are the
desktop equivalent of asking your developers for data-testid.

Re-discover these for any app with:
    CalculatorPage().open().window.print_control_identifiers()
"""

import re

from desktop.pages.base_app import BaseApp

# Automation ids for Calculator's keypad. Numbers follow an obvious
# pattern, so we build them instead of listing all ten by hand.
_OPERATOR_IDS = {
    "+": "plusButton",
    "-": "minusButton",
    "*": "multiplyButton",
    "/": "divideButton",
}


class CalculatorPage(BaseApp):
    app_path = "calc.exe"
    window_title = "Calculator"

    def _click(self, automation_id: str):
        """
        Find a button by its automation id and click it.

        We use .click(), which asks UI Automation to invoke the button
        directly, rather than .click_input(), which moves the real mouse
        pointer to the button's screen coordinates and clicks there.

        click_input() is the more realistic simulation, but it clicks
        whatever is at those coordinates AT THAT MOMENT - so anything
        that steals the foreground mid-test (a notification, another
        window opening) silently eats the click and the test fails for a
        reason nothing in the output explains. We hit exactly that while
        building this suite. .click() targets the control itself, so it
        can't be intercepted.

        Prefer click_input() only when the realism is the point (testing
        that a button isn't covered by something), and call
        window.set_focus() first when you do.
        """
        self.window.child_window(
            auto_id=automation_id, control_type="Button"
        ).click()

    def press_number(self, number: int):
        """Press each digit of `number` in order, e.g. press_number(42) -> 4, 2."""
        for digit in str(number):
            self._click(f"num{digit}Button")

    def press_operator(self, operator: str):
        """Press an operator button: one of + - * /."""
        self._click(_OPERATOR_IDS[operator])

    def press_equals(self):
        self._click("equalButton")

    def clear(self):
        """Reset the display to 0, so tests always start from a clean state."""
        self._click("clearButton")

    def result_text(self) -> str:
        """
        The result display's full accessible text, e.g. "Display is 12".

        Calculator's display is a Text control whose NAME carries the
        value - so unlike a web input, there is no "value" to read; we
        read the label UI Automation exposes.
        """
        return self.window.child_window(
            auto_id="CalculatorResults", control_type="Text"
        ).window_text()

    def result_value(self) -> str:
        """
        Just the number part of result_text(), e.g. "12".

        The prefix ("Display is ") is localized, so we don't strip it by
        name - we pull the trailing number out instead, and drop any
        thousands separators so "1,000" compares as "1000".
        """
        match = re.search(r"-?[\d.,]+$", self.result_text())
        return match.group().replace(",", "") if match else ""
