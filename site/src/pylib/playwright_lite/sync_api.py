"""playwright_lite - the real Playwright sync API, running in the browser.

Learners import this as `from playwright.sync_api import Page, expect`
(see learner_env/playwright/), so anything they write here can be pasted
straight into the kit's own tests and run against a real browser.

Three things are deliberately faithful, because they are the things
beginners actually get wrong:

  * AUTO-WAITING. Every action retries until the element is actionable
    or the timeout runs out. The retry loop lives here, in Python, and
    advances the app's virtual clock as it polls - so "the element
    appears after 600 ms" is taught exactly, and identically on every
    run.
  * STRICT MODE. Two matches is an error, not a coin flip. That is why
    the kit's Test Case 7 needs .first.
  * ERROR MESSAGES. The wording below matches what real Playwright
    prints, including the "Call log:" block, because reading those
    messages is half the skill.

What it is NOT: a browser. There are no frames, no network, no
downloads, no screenshots. Anything missing raises a clear
NotImplementedError rather than quietly doing nothing.
"""

import json

from . import _runtime

# Playwright's own defaults: 30 s for actions, 5 s for expect().
DEFAULT_TIMEOUT = 30_000
_expect_timeout = 5_000

# How far the virtual clock jumps between retries. Fine-grained at first
# so a 600 ms round trip resolves at exactly 600 ms, coarser afterwards
# so a genuinely failing test reports quickly.
_FINE_POLL = 100
_COARSE_POLL = 500
_FINE_WINDOW = 1_000


class Error(Exception):
    """Base class for every Playwright error (playwright.sync_api.Error)."""


class TimeoutError(Error):
    """Raised when an action or assertion runs out of time.

    Yes, it shadows the builtin - so does the real
    playwright.sync_api.TimeoutError, and matching it matters more here
    than avoiding the shadow.
    """


# --------------------------------------------------------------------------
# Turning a locator chain back into the code that built it
# --------------------------------------------------------------------------

def _q(value):
    """Quote a string the way Playwright prints it in a call log."""
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def _describe_step(step):
    kind = step["k"]
    if kind in ("css", "xpath"):
        return f"locator({_q(step['v'])})"
    if kind == "role":
        parts = [_q(step["role"])]
        if step.get("name") is not None:
            parts.append(f"name={_q(step['name'])}")
        if step.get("exact"):
            parts.append("exact=True")
        return f"get_by_role({', '.join(parts)})"
    if kind == "filter":
        parts = []
        if step.get("hasText") is not None:
            parts.append(f"has_text={_q(step['hasText'])}")
        if step.get("hasNotText") is not None:
            parts.append(f"has_not_text={_q(step['hasNotText'])}")
        return f"filter({', '.join(parts)})"
    if kind == "nth":
        return f"nth({step['v']})"
    if kind in ("first", "last"):
        return kind
    simple = {
        "text": "get_by_text", "label": "get_by_label",
        "placeholder": "get_by_placeholder", "testid": "get_by_test_id",
        "alttext": "get_by_alt_text", "title": "get_by_title",
    }
    if kind in simple:
        suffix = ", exact=True" if step.get("exact") else ""
        return f"{simple[kind]}({_q(step['v'])}{suffix})"
    return kind


def _describe(chain):
    return ".".join(_describe_step(step) for step in chain)


def _selector_step(selector):
    """Split Playwright's engine prefixes off a raw selector string."""
    text = selector.strip()
    if text.startswith("xpath="):
        return {"k": "xpath", "v": text[6:]}
    if text.startswith(("//", "(//", "..")):
        return {"k": "xpath", "v": text}
    if text.startswith("text="):
        return {"k": "text", "v": text[5:]}
    if text.startswith("css="):
        return {"k": "css", "v": text[4:]}
    return {"k": "css", "v": text}


# --------------------------------------------------------------------------
# Locator
# --------------------------------------------------------------------------

class Locator:
    """An address for one or more elements. Creating it touches nothing;
    every action re-finds the element from scratch."""

    def __init__(self, chain):
        self._chain = list(chain)

    # ---------------------------------------------------------- building

    def locator(self, selector):
        return Locator(self._chain + [_selector_step(selector)])

    def get_by_role(self, role, name=None, exact=False):
        return Locator(self._chain + [
            {"k": "role", "role": role, "name": name, "exact": bool(exact)}
        ])

    def get_by_text(self, text, exact=False):
        return Locator(self._chain + [{"k": "text", "v": text, "exact": bool(exact)}])

    def get_by_label(self, text, exact=False):
        return Locator(self._chain + [{"k": "label", "v": text, "exact": bool(exact)}])

    def get_by_placeholder(self, text, exact=False):
        return Locator(self._chain + [{"k": "placeholder", "v": text, "exact": bool(exact)}])

    def get_by_test_id(self, test_id):
        return Locator(self._chain + [{"k": "testid", "v": test_id}])

    def get_by_alt_text(self, text, exact=False):
        return Locator(self._chain + [{"k": "alttext", "v": text, "exact": bool(exact)}])

    def get_by_title(self, text, exact=False):
        return Locator(self._chain + [{"k": "title", "v": text, "exact": bool(exact)}])

    def filter(self, has_text=None, has_not_text=None):
        return Locator(self._chain + [
            {"k": "filter", "hasText": has_text, "hasNotText": has_not_text}
        ])

    @property
    def first(self):
        return Locator(self._chain + [{"k": "first"}])

    @property
    def last(self):
        return Locator(self._chain + [{"k": "last"}])

    def nth(self, index):
        return Locator(self._chain + [{"k": "nth", "v": index}])

    def __repr__(self):
        return f"<Locator {_describe(self._chain)}>"

    # ----------------------------------------------------------- internals

    def _chain_json(self):
        return json.dumps(self._chain)

    def _once(self, action, args=()):
        """One attempt. Returns the parsed {ok, value} / {ok, code} dict."""
        return json.loads(_runtime.BRIDGE.perform(
            self._chain_json(), action, json.dumps(list(args)), -1
        ))

    def _strict_error(self, method, count):
        described = _describe(self._chain)
        info = json.loads(_runtime.BRIDGE.describe(self._chain_json()))
        headline = (f"Locator.{method}: Error: strict mode violation: "
                    f"{described} resolved to {count} elements:")
        lines = [headline]
        for index, sample in enumerate(info["samples"], start=1):
            lines.append(f"    {index}) {sample}")
        lines.append("")
        lines.append("Add .first, .nth(i) or a more specific locator to pick one.")
        return Error("\n".join(lines))

    def _timeout_error(self, method, timeout, last):
        """Build the message Playwright would print - it is teaching material."""
        described = _describe(self._chain)
        log = [f"  - waiting for {described}"]
        code = (last or {}).get("code")
        detail = (last or {}).get("detail", "")
        if code == "not_visible":
            log.append("  - locator resolved to a hidden element")
            log.append(f"  - retrying {method} action")
        elif code == "not_enabled":
            log.append("  - element is not enabled")
            log.append(f"  - retrying {method} action")
        elif code == "not_editable":
            log.append("  - element is not an editable input")
        elif code == "intercepted":
            log.append(f"  - {detail} intercepts pointer events")
            log.append(f"  - retrying {method} action")
        elif code == "no_option":
            log.append("  - no <option> matched the value you asked for")
        return TimeoutError(
            f"Locator.{method}: Timeout {timeout}ms exceeded.\nCall log:\n"
            + "\n".join(log)
        )

    def _run(self, method, action=None, args=(), timeout=None):
        """Do something to the element, retrying until it is actionable."""
        action = action or method
        limit = DEFAULT_TIMEOUT if timeout is None else timeout
        waited = 0
        last = None
        while True:
            result = self._once(action, args)
            if result["ok"]:
                _runtime.record(method, _describe(self._chain), self._chain, args)
                return result["value"]
            code = result["code"]
            if code == "strict":
                # Strict violations are a bug in the locator, not a delay:
                # real Playwright fails immediately, and so do we.
                raise self._strict_error(method, int(result["detail"]))
            if code == "unsupported":
                raise NotImplementedError(
                    f"playwright_lite does not implement Locator.{action}() yet."
                )
            last = result
            if waited >= limit:
                _runtime.record(method, _describe(self._chain), self._chain, args,
                                ok=False, detail=code)
                raise self._timeout_error(method, limit, last)
            step = _FINE_POLL if waited < _FINE_WINDOW else _COARSE_POLL
            _runtime.BRIDGE.tick(step)
            waited += step

    # ------------------------------------------------------------- actions

    def click(self, timeout=None):
        self._run("click", timeout=timeout)

    def hover(self, timeout=None):
        self._run("hover", timeout=timeout)

    def focus(self, timeout=None):
        self._run("focus", timeout=timeout)

    def fill(self, value, timeout=None):
        self._run("fill", args=[value], timeout=timeout)

    def press(self, key, timeout=None):
        self._run("press", args=[key], timeout=timeout)

    def check(self, timeout=None):
        self._run("check", timeout=timeout)

    def uncheck(self, timeout=None):
        self._run("uncheck", timeout=timeout)

    def select_option(self, value=None, label=None, timeout=None):
        self._run("select_option", args=[value, label], timeout=timeout)

    def scroll_into_view_if_needed(self, timeout=None):
        self._run("scroll_into_view_if_needed", timeout=timeout)

    # --------------------------------------------------------------- reads

    def inner_text(self, timeout=None):
        return self._run("inner_text", timeout=timeout)

    def text_content(self, timeout=None):
        return self._run("text_content", timeout=timeout)

    def input_value(self, timeout=None):
        return self._run("input_value", timeout=timeout)

    def get_attribute(self, name, timeout=None):
        return self._run("get_attribute", args=[name], timeout=timeout)

    def count(self):
        """How many elements match right now. Never waits - this is the
        one place Playwright deliberately gives you a snapshot."""
        return int(_runtime.BRIDGE.count(self._chain_json()))

    def all_inner_texts(self):
        """Every match's text, as a plain list. Zero matches is fine here -
        this is the one read that does not insist on finding anything."""
        texts = json.loads(_runtime.BRIDGE.all_texts(self._chain_json()))
        # Recorded (unlike count(), which expect().to_have_count polls in a
        # loop) because a learner calls this once, on purpose.
        _runtime.record("all_inner_texts", _describe(self._chain), self._chain)
        return texts

    def _immediate(self, action, default):
        if self.count() == 0:
            return default
        result = self._once(action)
        if not result["ok"]:
            if result["code"] == "strict":
                raise self._strict_error(action, int(result["detail"]))
            return default
        _runtime.record(action, _describe(self._chain), self._chain)
        return result["value"]

    def is_visible(self):
        """A snapshot, NOT a wait. If you find yourself writing
        `assert locator.is_visible()`, you wanted expect(...) instead."""
        return bool(self._immediate("is_visible", False))

    def is_enabled(self):
        return bool(self._immediate("is_enabled", False))

    def is_checked(self):
        return bool(self._immediate("is_checked", False))

    def is_hidden(self):
        return not self.is_visible()


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

class Page:
    """One browser tab. The `page` fixture hands you one of these."""

    def locator(self, selector):
        return Locator([_selector_step(selector)])

    def get_by_role(self, role, name=None, exact=False):
        return Locator([{"k": "role", "role": role, "name": name, "exact": bool(exact)}])

    def get_by_text(self, text, exact=False):
        return Locator([{"k": "text", "v": text, "exact": bool(exact)}])

    def get_by_label(self, text, exact=False):
        return Locator([{"k": "label", "v": text, "exact": bool(exact)}])

    def get_by_placeholder(self, text, exact=False):
        return Locator([{"k": "placeholder", "v": text, "exact": bool(exact)}])

    def get_by_test_id(self, test_id):
        return Locator([{"k": "testid", "v": test_id}])

    def get_by_alt_text(self, text, exact=False):
        return Locator([{"k": "alttext", "v": text, "exact": bool(exact)}])

    def get_by_title(self, text, exact=False):
        return Locator([{"k": "title", "v": text, "exact": bool(exact)}])

    # ---------------------------------------------------------- navigation

    def goto(self, url):
        # Accept either a full address or a bare path, so both
        # page.goto(BASE_URL + "/login") and page.goto("/login") work.
        path = url
        for prefix in ("https://automationexercise.com", "http://automationexercise.com"):
            if path.startswith(prefix):
                path = path[len(prefix):]
                break
        if not path.startswith("/"):
            raise Error(f"page.goto: {url} is not a page of this practice site.")
        result = _runtime.BRIDGE.goto_path(path)
        _runtime.record("goto", path, [], [url])
        return result

    def reload(self):
        _runtime.record("reload", self.url, [])
        return _runtime.BRIDGE.reload()

    def go_back(self):
        _runtime.record("go_back", self.url, [])
        return _runtime.BRIDGE.go_back()

    @property
    def url(self):
        return _runtime.BRIDGE.url()

    def title(self):
        return _runtime.BRIDGE.title()

    def wait_for_timeout(self, milliseconds):
        """Playwright has this, and Playwright tells you not to use it.
        It is here so the lesson about it can be honest."""
        _runtime.record("wait_for_timeout", "", [], [milliseconds])
        _runtime.BRIDGE.tick(milliseconds)

    def __repr__(self):
        return f"<Page url={self.url!r}>"


# --------------------------------------------------------------------------
# expect()
# --------------------------------------------------------------------------

def _assertion_error(subject, expectation, actual, matcher, timeout, target):
    """The failure format from the guide's "What a failure looks like"."""
    lines = [
        f"{subject} expected {expectation}",
        f"Actual value: {actual}",
        "Call log:",
        f"  - expect({subject.lower()}).{matcher} with timeout {timeout}ms",
    ]
    if target:
        lines.append(f"  - waiting for {target}")
    return AssertionError("\n".join(lines))


class LocatorAssertions:
    def __init__(self, locator, timeout=None, is_not=False):
        self._locator = locator
        self._timeout = _expect_timeout if timeout is None else timeout
        self._is_not = is_not

    # -------------------------------------------------------------- engine

    def _poll(self, matcher, expectation, probe, timeout=None):
        """Retry `probe` until it reports success - the web-first wait
        that makes expect() different from a bare assert."""
        limit = self._timeout if timeout is None else timeout
        waited = 0
        actual = ""
        while True:
            ok, actual = probe()
            if ok != self._is_not:
                _runtime.record(
                    f"expect.{'not_' if self._is_not else ''}{matcher}",
                    _describe(self._locator._chain), self._locator._chain,
                )
                return
            if waited >= limit:
                _runtime.record(
                    f"expect.{'not_' if self._is_not else ''}{matcher}",
                    _describe(self._locator._chain), self._locator._chain,
                    ok=False, detail=str(actual),
                )
                phrase = ("not " if self._is_not else "") + expectation
                raise _assertion_error("Locator", phrase, actual, matcher,
                                       limit, _describe(self._locator._chain))
            step = _FINE_POLL if waited < _FINE_WINDOW else _COARSE_POLL
            _runtime.BRIDGE.tick(step)
            waited += step

    def _info(self):
        return json.loads(_runtime.BRIDGE.describe(self._locator._chain_json()))

    def _single_text(self):
        info = self._info()
        if info["count"] == 0:
            return None
        return info["texts"][0]

    # ------------------------------------------------------------ matchers

    def to_be_visible(self, timeout=None):
        self._poll("to_be_visible", "to be visible",
                   lambda: (self._info()["visible"] > 0, "hidden"), timeout)

    def not_to_be_visible(self, timeout=None):
        LocatorAssertions(self._locator, self._timeout, not self._is_not) \
            .to_be_visible(timeout)

    def to_be_hidden(self, timeout=None):
        self._poll("to_be_hidden", "to be hidden",
                   lambda: (self._info()["visible"] == 0, "visible"), timeout)

    def not_to_be_hidden(self, timeout=None):
        LocatorAssertions(self._locator, self._timeout, not self._is_not) \
            .to_be_hidden(timeout)

    def to_have_text(self, expected, timeout=None):
        def probe():
            text = self._single_text()
            return (text is not None and _norm(text) == _norm(expected),
                    "<no element found>" if text is None else text)
        self._poll("to_have_text", f"to have text {expected!r}", probe, timeout)

    def not_to_have_text(self, expected, timeout=None):
        LocatorAssertions(self._locator, self._timeout, not self._is_not) \
            .to_have_text(expected, timeout)

    def to_contain_text(self, expected, timeout=None):
        def probe():
            text = self._single_text()
            return (text is not None and _norm(expected) in _norm(text),
                    "<no element found>" if text is None else text)
        self._poll("to_contain_text", f"to contain text {expected!r}", probe, timeout)

    def not_to_contain_text(self, expected, timeout=None):
        LocatorAssertions(self._locator, self._timeout, not self._is_not) \
            .to_contain_text(expected, timeout)

    def to_have_value(self, expected, timeout=None):
        def probe():
            if self._locator.count() == 0:
                return False, "<no element found>"
            value = self._locator._once("input_value")
            actual = value.get("value") if value["ok"] else "<not an input>"
            return actual == expected, actual
        self._poll("to_have_value", f"to have value {expected!r}", probe, timeout)

    def to_have_count(self, expected, timeout=None):
        def probe():
            count = self._locator.count()
            return count == expected, count
        self._poll("to_have_count", f"to have count {expected}", probe, timeout)

    def to_have_attribute(self, name, value, timeout=None):
        def probe():
            if self._locator.count() == 0:
                return False, "<no element found>"
            result = self._locator._once("get_attribute", [name])
            actual = result.get("value") if result["ok"] else None
            return actual == value, actual
        self._poll("to_have_attribute", f"to have attribute {name}={value!r}",
                   probe, timeout)

    def to_be_enabled(self, timeout=None):
        self._poll("to_be_enabled", "to be enabled",
                   lambda: (self._locator.is_enabled(), "disabled"), timeout)

    def to_be_disabled(self, timeout=None):
        self._poll("to_be_disabled", "to be disabled",
                   lambda: (not self._locator.is_enabled(), "enabled"), timeout)

    def to_be_checked(self, timeout=None):
        self._poll("to_be_checked", "to be checked",
                   lambda: (self._locator.is_checked(), "unchecked"), timeout)

    def not_to_be_checked(self, timeout=None):
        LocatorAssertions(self._locator, self._timeout, not self._is_not) \
            .to_be_checked(timeout)

    def to_be_empty(self, timeout=None):
        self._poll("to_be_empty", "to be empty",
                   lambda: (_norm(self._single_text() or "") == "",
                            self._single_text()), timeout)


class PageAssertions:
    def __init__(self, page, timeout=None):
        self._page = page
        self._timeout = _expect_timeout if timeout is None else timeout

    def _poll(self, matcher, expectation, probe, subject_actual, timeout=None):
        limit = self._timeout if timeout is None else timeout
        waited = 0
        while True:
            if probe():
                _runtime.record(f"expect.{matcher}", "page", [])
                return
            if waited >= limit:
                _runtime.record(f"expect.{matcher}", "page", [], ok=False)
                raise _assertion_error("Page", expectation, subject_actual(),
                                       matcher, limit, None)
            step = _FINE_POLL if waited < _FINE_WINDOW else _COARSE_POLL
            _runtime.BRIDGE.tick(step)
            waited += step

    def to_have_url(self, expected, timeout=None):
        self._poll("to_have_url", f"to have URL {expected!r}",
                   lambda: self._page.url == expected,
                   lambda: self._page.url, timeout)

    def to_have_title(self, expected, timeout=None):
        self._poll("to_have_title", f"to have title {expected!r}",
                   lambda: self._page.title() == expected,
                   lambda: self._page.title(), timeout)


def _norm(text):
    return " ".join(str(text).split())


def expect(subject, timeout=None):
    """Playwright's web-first assertion. It RETRIES until the condition
    holds or the timeout runs out - which is why you never need a sleep."""
    if isinstance(subject, Page):
        return PageAssertions(subject, timeout)
    if isinstance(subject, Locator):
        return LocatorAssertions(subject, timeout)
    raise Error(
        "expect() takes a Page or a Locator. "
        f"You passed {type(subject).__name__} - did you call .inner_text() "
        "or .count() by mistake? Those give plain values, so they need a "
        "plain assert (and lose the automatic waiting)."
    )


def _set_options(timeout=None):
    """expect.set_options(timeout=...) - matches fixtures/browser.py."""
    global _expect_timeout
    if timeout is not None:
        _expect_timeout = timeout


expect.set_options = _set_options
