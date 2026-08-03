"""Unit tests for playwright_lite - no browser, no Pyodide.

The shim is deliberately split so this is possible: it never touches the
DOM itself, it only asks a "bridge" object to. Swap in a fake bridge and
the interesting half - the auto-wait retry loop, strict mode, and the
wording of the error messages - can be tested in milliseconds.

The other half (which elements a selector actually matches) lives in
JavaScript and is covered by the browser tests in this same folder.
"""

import importlib
import json
import sys
from pathlib import Path

import pytest

# playwright_lite lives beside the site's other browser assets. Adding
# that folder to sys.path is safe: the directory that would shadow the
# REAL playwright package (learner_env/) is one level deeper, so
# `import playwright` here still finds the installed one.
PYLIB = Path(__file__).resolve().parents[1] / "src" / "pylib"
if str(PYLIB) not in sys.path:
    sys.path.insert(0, str(PYLIB))

sync_api = importlib.import_module("playwright_lite.sync_api")
runtime = importlib.import_module("playwright_lite._runtime")
rubric = importlib.import_module("quest.rubric")


class FakeBridge:
    """A stand-in for the DOM.

    Elements are described by the LAST step of the locator chain, which
    is all these tests need: {"#results": {"appears": 600, "count": 1}}.
    Nothing exists before its `appears` time, so advancing the virtual
    clock is the only way to make an element show up - exactly the
    situation auto-waiting exists for.
    """

    def __init__(self, elements=None):
        self.elements = elements or {}
        self.moment = 0
        self.ticks = []

    # -- helpers ---------------------------------------------------------
    def _spec(self, chain_json):
        chain = json.loads(chain_json)
        narrowed = any(step["k"] in ("first", "last", "nth") for step in chain)
        searching = [s for s in chain if s["k"] not in ("first", "last", "nth", "filter")]
        last = searching[-1] if searching else chain[-1]
        key = last.get("v", last.get("name", ""))
        spec = self.elements.get(key)
        if spec is None or self.moment < spec.get("appears", 0):
            return {"count": 0, "visible": 0}
        if narrowed:
            # .first / .nth() narrow the set to one, which is how they
            # rescue a locator from a strict-mode violation.
            return dict(spec, count=min(spec.get("count", 0), 1),
                        visible=min(spec.get("visible", 0), 1))
        return spec

    # -- the bridge interface -------------------------------------------
    def now(self):
        return self.moment

    def tick(self, ms):
        self.moment += ms
        self.ticks.append(ms)
        return self.moment

    def count(self, chain_json):
        return self._spec(chain_json).get("count", 0)

    def describe(self, chain_json):
        spec = self._spec(chain_json)
        count = spec.get("count", 0)
        return json.dumps({
            "count": count,
            "visible": spec.get("visible", count),
            "samples": ["<button#fake>"] * min(count, 5),
            "texts": [spec.get("text", "")] * min(count, 5),
        })

    def perform(self, chain_json, action, args_json, _index):
        spec = self._spec(chain_json)
        count = spec.get("count", 0)
        if count == 0:
            return json.dumps({"ok": False, "code": "not_found", "detail": ""})
        if count > 1:
            return json.dumps({"ok": False, "code": "strict", "detail": str(count)})
        if action == "is_visible":
            return json.dumps({"ok": True, "value": spec.get("visible", 1) > 0})
        if action == "inner_text":
            return json.dumps({"ok": True, "value": spec.get("text", "")})
        if action == "input_value":
            return json.dumps({"ok": True, "value": spec.get("value", "")})
        if not spec.get("visible", 1):
            return json.dumps({"ok": False, "code": "not_visible", "detail": ""})
        json.loads(args_json)          # prove the args are serialisable
        return json.dumps({"ok": True, "value": None})

    def all_texts(self, chain_json):
        spec = self._spec(chain_json)
        return json.dumps([spec.get("text", "")] * spec.get("count", 0))

    def url(self):
        return "https://automationexercise.com/products"

    def title(self):
        return "Automation Exercise"

    def goto_path(self, path):
        return "https://automationexercise.com" + path


@pytest.fixture
def bridge():
    """Bind a fresh fake bridge for one test, then unbind it."""
    fake = FakeBridge()
    runtime.bind(fake)
    runtime.reset_log()
    yield fake
    runtime.bind(None)


@pytest.fixture
def page():
    return sync_api.Page()


# ---------------------------------------------------------------- actions

def test_fill_reaches_the_element_and_is_logged(bridge, page):
    bridge.elements["#search_product"] = {"count": 1, "visible": 1}

    page.locator("#search_product").fill("dress")

    entry = runtime.ACTION_LOG[-1]
    assert entry["method"] == "fill"
    assert entry["args"] == ["dress"]
    # The log records WHICH KIND of locator was used, which is how
    # challenges can require a role-based locator without reading source.
    assert entry["kinds"] == ["css"]


def test_a_missing_element_times_out_with_playwright_wording(bridge, page):
    with pytest.raises(sync_api.TimeoutError) as caught:
        page.locator("#nope").click(timeout=1_000)

    message = str(caught.value)
    assert message.startswith("Locator.click: Timeout 1000ms exceeded.")
    assert "Call log:" in message
    assert 'waiting for locator("#nope")' in message


def test_two_matches_is_a_strict_mode_violation_not_a_coin_flip(bridge, page):
    bridge.elements["Test Cases"] = {"count": 2, "visible": 2}

    with pytest.raises(sync_api.Error) as caught:
        page.get_by_role("link", name="Test Cases").click()

    message = str(caught.value)
    assert "strict mode violation" in message
    assert "resolved to 2 elements" in message
    # And it fails immediately - retrying would never help.
    assert bridge.ticks == []


def test_first_resolves_the_strict_mode_violation(bridge, page):
    bridge.elements["Test Cases"] = {"count": 2, "visible": 2}

    page.get_by_role("link", name="Test Cases").first.click()

    assert runtime.ACTION_LOG[-1]["method"] == "click"


# ------------------------------------------------------------- auto-wait

def test_expect_waits_for_an_element_that_arrives_later(bridge, page):
    bridge.elements["Searched Products"] = {"count": 1, "visible": 1, "appears": 600}

    sync_api.expect(page.get_by_text("Searched Products")).to_be_visible()

    # It waited exactly as long as it had to - not a millisecond more.
    assert bridge.moment == 600


def test_is_visible_does_not_wait_at_all(bridge, page):
    bridge.elements[".productinfo"] = {"count": 1, "visible": 1, "appears": 600}

    # This is the mistake the rubric warns about: a snapshot, taken too
    # early, that a sleep would "fix" and expect() solves properly.
    assert page.locator(".productinfo").is_visible() is False
    assert bridge.moment == 0


def test_a_failed_expect_reads_like_the_guides_example(bridge, page):
    with pytest.raises(AssertionError) as caught:
        sync_api.expect(page.get_by_text("Order placed!")).to_be_visible(timeout=500)

    message = str(caught.value)
    assert message.splitlines()[0] == "Locator expected to be visible"
    assert "Actual value: hidden" in message
    assert "- expect(locator).to_be_visible with timeout 500ms" in message
    assert '- waiting for get_by_text("Order placed!")' in message


def test_to_have_count_reports_the_number_it_saw(bridge, page):
    bridge.elements[".productinfo"] = {"count": 3, "visible": 3}

    sync_api.expect(page.locator(".productinfo")).to_have_count(3)

    with pytest.raises(AssertionError) as caught:
        sync_api.expect(page.locator(".productinfo")).to_have_count(5, timeout=200)
    assert "Actual value: 3" in str(caught.value)


# -------------------------------------------------------------- locators

def test_chained_locators_describe_themselves_the_way_they_were_written(page):
    locator = (sync_api.Page().locator(".shop-menu")
               .get_by_role("link", name="Cart").first)

    assert repr(locator) == (
        '<Locator locator(".shop-menu").get_by_role("link", name="Cart").first>'
    )


def test_xpath_and_text_engine_prefixes_are_understood(page):
    assert page.locator("//button")._chain == [{"k": "xpath", "v": "//button"}]
    assert page.locator("text=Cart")._chain == [{"k": "text", "v": "Cart"}]


def test_expect_on_a_plain_value_explains_the_mistake(bridge, page):
    bridge.elements[".productinfo"] = {"count": 1, "visible": 1, "text": "Blue Top"}

    with pytest.raises(sync_api.Error) as caught:
        sync_api.expect(page.locator(".productinfo").inner_text())

    assert "expect() takes a Page or a Locator" in str(caught.value)


# ---------------------------------------------------------------- rubric

def test_rubric_rejects_time_sleep_with_a_reason_not_just_a_no():
    findings = rubric.review(
        "import time\n"
        "def test_thing(page):\n"
        "    page.locator('#go').click()\n"
        "    time.sleep(2)\n"
    )

    sleep = [f for f in findings if f["rule"] == "no-sleep"]
    assert len(sleep) == 1
    assert sleep[0]["severity"] == "error"
    assert sleep[0]["line"] == 4
    assert "expect(" in sleep[0]["message"]


def test_rubric_rejects_assert_is_visible_and_names_the_matcher():
    findings = rubric.review(
        "def test_thing(page):\n"
        "    assert page.get_by_text('Hi').is_visible()\n",
        ["expect-over-assert"],
    )

    assert findings[0]["rule"] == "expect-over-assert"
    assert "to_be_visible()" in findings[0]["message"]


def test_rubric_leaves_a_legitimate_plain_assert_alone():
    # Test Case 9 does exactly this, and it is correct: the value was
    # already read into a variable, so there is nothing left to wait for.
    findings = rubric.review(
        "def test_thing(page):\n"
        "    names = page.locator('.productinfo p').all_inner_texts()\n"
        "    assert len(names) > 0\n",
        ["expect-over-assert", "has-assertion"],
    )

    assert findings == []


def test_rubric_flags_a_missing_test_function():
    findings = rubric.review("page.locator('#a').click()\n", ["test-function"])

    assert findings[0]["rule"] == "test-function"
    assert "test_" in findings[0]["message"]
