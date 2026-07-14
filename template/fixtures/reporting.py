"""
fixtures/reporting.py
=====================
Everything that makes the test REPORTS better:

  1. A bug fix so the HTML report saves correctly on Windows
  2. A screenshot of the page attached to Allure when a test fails
  3. Feature-area labels so Allure can group results per part of the app
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
# anything outside that set, saving the report crashes at the very end of
# the run. The fix: replace the plugin's save method with a copy that
# writes UTF-8, the encoding the report's own <meta charset> promises.


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
# is worth a thousand stack traces.


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    # report.when is "setup", "call" (the test itself) or "teardown".
    # We stash each phase's result, e.g. item.rep_call for the test body.
    setattr(item, "rep_" + report.when, report)


@pytest.fixture(autouse=True)
def screenshot_on_failure(page: Page, request):
    yield  # let the test run first

    report = getattr(request.node, "rep_call", None)
    if report is None or not report.failed:
        return  # test passed (or never ran) -> no screenshot needed

    # A screenshot failure should never hide the REAL test failure —
    # so we try, and quietly give up if the browser is in a bad state.
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
# Map feature areas of YOUR app to filename fragments of the tests that
# cover them. Allure then groups results per area, so you can see WHERE
# failures cluster instead of just how many failed. Example:
#
# FEATURE_AREAS = {
#     "Authentication": ["login", "signup", "logout"],
#     "Dashboard":      ["dashboard"],
# }

FEATURE_AREAS = {}


def pytest_collection_modifyitems(items):
    """Attach the matching Allure feature label to every collected test."""
    for item in items:
        for feature, fragments in FEATURE_AREAS.items():
            if any(fragment in item.nodeid for fragment in fragments):
                item.add_marker(allure.feature(feature))
                break
