"""The code-review rubric: the kit's conventions, enforced with `ast`.

Why an AST and not a regular expression? Because grading must be about
what the code MEANS. `# never use time.sleep` is a comment, not a sleep;
`assert page.get_by_text("Cart").is_visible()` is a real problem even
though it contains the word "expect" nowhere. Parsing gets both right.

Every finding is written in the voice of a senior reviewer leaving a
kind, specific comment on a pull request - because a red X teaches
nothing, and "no time.sleep" without the reason teaches only obedience.

Severities:
    error   - blocks the challenge. A reviewer would not approve this.
    advice  - passes, but costs the clean-run bonus. Worth knowing.
"""

import ast

# Methods that answer "what is true RIGHT NOW" and never wait. Wrapping
# one in a bare assert throws away Playwright's auto-waiting, which is
# the single most common cause of flaky beginner tests.
SNAPSHOT_MATCHERS = {
    "is_visible": "expect(locator).to_be_visible()",
    "is_hidden": "expect(locator).to_be_hidden()",
    "is_enabled": "expect(locator).to_be_enabled()",
    "is_checked": "expect(locator).to_be_checked()",
    "count": "expect(locator).to_have_count(n)",
    "inner_text": "expect(locator).to_have_text(...) or .to_contain_text(...)",
    "text_content": "expect(locator).to_have_text(...)",
    "input_value": "expect(locator).to_have_value(...)",
    "get_attribute": "expect(locator).to_have_attribute(name, value)",
}

LOCATOR_BUILDERS = {
    "locator", "get_by_role", "get_by_text", "get_by_label",
    "get_by_placeholder", "get_by_test_id", "get_by_alt_text", "get_by_title",
}


def _finding(rule, severity, node, title, message):
    return {
        "rule": rule,
        "severity": severity,
        # A whole-file finding (no assertion anywhere, no test function)
        # has no node of its own, so point at the first line rather than
        # at a meaningless line 0.
        "line": getattr(node, "lineno", None) or _first_line(node),
        "title": title,
        "message": message,
    }


def _first_line(node):
    body = getattr(node, "body", None)
    if body:
        return getattr(body[0], "lineno", 1)
    return 1


def _calls(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def _attr_name(node):
    """The method name of `something.method(...)`, else None."""
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _first_string_arg(node):
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


# --------------------------------------------------------------------------
# The rules
# --------------------------------------------------------------------------

def rule_no_sleep(tree, _config):
    """time.sleep() and wait_for_timeout() - fixed waits, always wrong."""
    findings = []
    for node in _calls(tree):
        name = _attr_name(node)
        is_sleep = name == "sleep" or (
            isinstance(node.func, ast.Name) and node.func.id == "sleep"
        )
        if is_sleep:
            findings.append(_finding(
                "no-sleep", "error", node,
                "Replace the sleep with an expect()",
                "A fixed sleep is wrong twice over: too short on a slow day "
                "(the test fails for no reason) and too long on a fast day "
                "(every run pays for it). Whatever you are waiting FOR, there "
                "is an expect() that says it out loud - expect(...)"
                ".to_be_visible(), .to_have_text(), .to_have_count() - and it "
                "waits exactly as long as needed, no longer. Tell me what you "
                "were waiting for and we will find the matcher together.",
            ))
        if name == "wait_for_timeout":
            findings.append(_finding(
                "no-sleep", "error", node,
                "wait_for_timeout() is a sleep in a Playwright costume",
                "It really is in the API, and Playwright's own docs tell you "
                "not to use it. Same reasoning as time.sleep(): it waits a "
                "guessed amount instead of waiting for the thing you actually "
                "care about. Use an expect() on the element that proves the "
                "page is ready.",
            ))
    return findings


def rule_expect_over_assert(tree, _config):
    """`assert locator.is_visible()` where expect() belongs."""
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        for call in [n for n in ast.walk(node.test) if isinstance(n, ast.Call)]:
            name = _attr_name(call)
            if name in SNAPSHOT_MATCHERS:
                findings.append(_finding(
                    "expect-over-assert", "error", node,
                    f"Use expect() instead of assert ....{name}()",
                    f".{name}() answers 'is this true at this exact "
                    "millisecond?' and never waits, so this assert passes or "
                    "fails depending on how busy the machine was - the "
                    "definition of a flaky test. Rewrite it as "
                    f"{SNAPSHOT_MATCHERS[name]}, which retries until the page "
                    "catches up. Keep the plain assert for values you have "
                    "already read into a variable (comparing two prices, "
                    "checking a list length) - that is the right tool there.",
                ))
    return findings


def rule_has_assertion(tree, _config):
    """A script with no assertion is not a test."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            return []
        is_expect_call = (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "expect"
        )
        if is_expect_call:
            return []
    return [_finding(
        "has-assertion", "error", tree,
        "This script never checks anything",
        "It drives the page perfectly well, but without an assertion it can "
        "never fail - so it can never tell you the site broke. Add the "
        "expect() that states what you believe should be true once the "
        "actions are done. That line is the reason the test exists.",
    )]


def rule_no_xpath(tree, _config):
    findings = []
    for node in _calls(tree):
        if _attr_name(node) != "locator":
            continue
        selector = _first_string_arg(node)
        if selector and selector.startswith(("//", "xpath=")):
            findings.append(_finding(
                "no-xpath", "advice", node,
                "An XPath here, where a role locator would read better",
                "XPath works, and one day you will need it. But it describes "
                "the page's internal shape, so it breaks the moment a "
                "developer wraps something in a new <div> - and the next "
                "person to read it has to decode it. Reach for "
                "get_by_role(...) first: it finds the element the way a user "
                "would, by what it IS and what it SAYS.",
            ))
    return findings


def rule_prefer_role_locator(tree, _config):
    """Advisory nudge in the zone where role locators were just taught."""
    findings = []
    for node in _calls(tree):
        if _attr_name(node) != "locator":
            continue
        selector = _first_string_arg(node)
        if selector and selector.startswith(("#", ".")):
            findings.append(_finding(
                "prefer-role-locator", "advice", node,
                f"Could {selector!r} be a get_by_role() instead?",
                "This works and it is not a crime - the kit itself uses "
                "#search_product, because that box has no visible label to "
                "grab. But CSS ties your test to the page's internals. When "
                "the element has a visible name (a button, a link, a "
                "heading), get_by_role(...) survives redesigns that would "
                "break a class selector.",
            ))
    return findings


def rule_no_locators_here(tree, config):
    """Page Object Model: the test file must contain no locators at all."""
    findings = []
    for node in _calls(tree):
        name = _attr_name(node)
        if name in LOCATOR_BUILDERS:
            findings.append(_finding(
                "no-locators-here", "error", node,
                f"A locator has escaped into {config.get('cell_label', 'the test')}",
                "Layering is the whole point of the exercise: tests say WHAT "
                "should be true, page objects know WHERE things are. Move "
                f".{name}(...) into the page object and give it a method name "
                "that reads like a user's intent - login(), add_to_cart(), "
                "search_for(). Then the day the markup changes you fix one "
                "line in one file instead of hunting through every test.",
            ))
    return findings


def rule_test_function(tree, _config):
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    if not functions:
        return [_finding(
            "test-function", "error", tree, "pytest needs a test function",
            "pytest collects functions whose NAME starts with test_ - that is "
            "the whole discovery rule. Wrap your code in one, for example "
            "def test_search_for_a_dress(page):, and pytest will find it.",
        )]
    if not any(f.name.startswith("test_") for f in functions):
        first = functions[0]
        return [_finding(
            "test-function", "error", first,
            f"Rename {first.name}() so pytest can find it",
            "pytest only collects functions whose name starts with test_. "
            f"As written, {first.name}() is just a function that nobody calls. "
            "Name it after the behaviour it proves - "
            "test_search_shows_matching_products - so a red line in CI tells "
            "you what broke before you open the file.",
        )]
    return []


RULES = {
    "no-sleep": rule_no_sleep,
    "expect-over-assert": rule_expect_over_assert,
    "has-assertion": rule_has_assertion,
    "no-xpath": rule_no_xpath,
    "prefer-role-locator": rule_prefer_role_locator,
    "no-locators-here": rule_no_locators_here,
    "test-function": rule_test_function,
}

# Applied to every challenge whether it asks for them or not. These two
# are the kit's non-negotiables.
ALWAYS = ["no-sleep"]


def review(source, requested=None, config=None):
    """Run the rubric over one piece of learner code.

    `requested` is the challenge's rubric list: names, or
    {"rule": name, "severity": "advice"} to soften one.
    Returns [] for code that parses; a SyntaxError propagates to the
    caller, which reports it with the line number.
    """
    tree = ast.parse(source)
    config = config or {}

    wanted = {name: None for name in ALWAYS}
    for entry in requested or []:
        if isinstance(entry, str):
            wanted[entry] = None
        else:
            wanted[entry["rule"]] = entry.get("severity")

    findings = []
    for name, override in wanted.items():
        rule = RULES.get(name)
        if rule is None:
            continue
        for finding in rule(tree, config):
            if override:
                finding["severity"] = override
            findings.append(finding)

    findings.sort(key=lambda f: (f["severity"] != "error", f["line"]))
    return findings
