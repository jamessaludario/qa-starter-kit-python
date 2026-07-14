"""
fixtures/reporting.py
=====================
Everything that makes the test REPORTS better:

  1. A bug fix so the HTML report saves correctly on Windows
  2. A screenshot of the page attached to Allure when a test fails
  3. Feature-area labels so Allure can group results per part of the site
"""

import allure
import pytest
import pytest_html.html_report
from playwright.sync_api import Page

# ---------------------------------------------------------------------------
# 1. Bug fix: always save the HTML report as UTF-8
# ---------------------------------------------------------------------------
# pytest-html 3.x saves report.html using Windows' default text encoding
# (cp1252), which only knows ~250 characters. If a failure message contains
# anything outside that set — like the icon-font characters this site uses —
# saving the report crashes at the very end of the run with
# "UnicodeEncodeError: 'charmap' codec can't encode character".
# The fix: replace the plugin's save method with a copy that writes UTF-8,
# the encoding the report's own <meta charset="utf-8"> header promises.


def _save_report_utf8(self, report_content):
    dir_name = self.logfile.parent
    assets_dir = dir_name / "assets"

    dir_name.mkdir(parents=True, exist_ok=True)
    if not self.self_contained:
        assets_dir.mkdir(parents=True, exist_ok=True)

    self.logfile.write_text(report_content, encoding="utf-8")
    if not self.self_contained:
        (assets_dir / "style.css").write_text(self.style_css, encoding="utf-8")


pytest_html.html_report.HTMLReport._save_report = _save_report_utf8


# ---------------------------------------------------------------------------
# 2. Screenshot on failure (attached to the Allure report)
# ---------------------------------------------------------------------------
# When a test fails, a picture of what the page looked like at that moment
# is worth a thousand stack traces. These two pieces work together:
#
#   - pytest normally keeps each test's result to itself. The hook copies
#     the result onto the test item, so the fixture below can read it.
#   - The autouse fixture runs after every test; if the test failed, it
#     takes one screenshot and attaches it to that test in Allure
#     (open a failed test in the report to see it).


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # report.when is "setup", "call" (the test itself) or "teardown".
    # We stash each phase's result, e.g. item.rep_call for the test body.
    setattr(item, "rep_" + report.when, report)


@pytest.fixture(autouse=True)
def screenshot_on_failure(page: Page, request):
    # Everything before `yield` runs BEFORE the test, everything after
    # runs AFTER it — so this line means "let the test run first".
    yield

    report = getattr(request.node, "rep_call", None)
    if report is None or not report.failed:
        return  # test passed (or never ran) -> no screenshot needed

    # The browser can be in a bad state after some failures (e.g. crashed
    # or already closed), and a screenshot failure should never hide the
    # REAL test failure — so we try, and quietly give up if we can't.
    try:
        allure.attach(
            page.screenshot(full_page=True),
            name="screenshot-at-failure",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 3. Feature areas (powers Allure's "Behaviors" view)
# ---------------------------------------------------------------------------
# Each test is tagged with the part of the website it covers. Allure then
# groups results per area on its Behaviors tab, so you can see at a glance
# WHERE failures cluster ("3 of 4 Cart tests failed") instead of just how
# many failed overall — in QA terms, the defect density per feature area.
#
# The usual way is an @allure.feature("Cart") decorator on every test.
# Keeping ONE map here does the same thing without editing 26 files, and
# doubles as a table of contents for the suite.

FEATURE_AREAS = {
    "Signup & Login":       ["tc01", "tc02", "tc03", "tc04", "tc05"],
    "Contact & Info Pages": ["tc06", "tc07"],
    "Products & Search":    ["tc08", "tc09", "tc18", "tc19", "tc21", "tc22"],
    "Subscription":         ["tc10", "tc11"],
    "Cart":                 ["tc12", "tc13", "tc17", "tc20"],
    "Checkout & Orders":    ["tc14", "tc15", "tc16", "tc23", "tc24"],
    "Home Page UI":         ["tc25", "tc26"],
}


def pytest_collection_modifyitems(items):
    """
    pytest calls this once, after it has found ("collected") all the tests.
    We look up each test's tcXX number in the map above and attach the
    matching Allure feature label to it.
    """
    for item in items:
        for feature, test_cases in FEATURE_AREAS.items():
            if any(tc in item.nodeid for tc in test_cases):
                item.add_marker(allure.feature(feature))
                break
