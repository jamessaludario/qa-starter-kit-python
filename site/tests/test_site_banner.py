"""
The verdict banner, the hints, and the accent picker.

The banner exists because of one complaint: clearing a challenge meant
scrolling to find the way on. So the two things a learner wants the
instant a run ends - did it pass, and what now - are said once at the
top and stuck there.

The banner tests need a real run, so they are `slow`. The hint and
accent tests do not touch Python and stay fast.
"""

import pytest
from pages.challenge_page import RUN_TIMEOUT_MS, ChallengePage
from pages.map_page import MapPage
from playwright.sync_api import Page, expect

FIRST = "base-camp", "first-test"

CORRECT = '''from playwright.sync_api import Page, expect


def test_home_page_has_the_right_title(page: Page):
    page.goto("https://automationexercise.com/")
    expect(page).to_have_title("Automation Exercise")
'''

WITH_A_SLEEP = '''import time

from playwright.sync_api import Page, expect


def test_home_page_has_the_right_title(page: Page):
    page.goto("https://automationexercise.com/")
    time.sleep(2)
    expect(page).to_have_title("Automation Exercise")
'''

WRONG_TITLE = CORRECT.replace("Automation Exercise", "Not The Title")


# --------------------------------------------------------------------------
# Hints - no Python needed
# --------------------------------------------------------------------------

def test_a_hint_is_hidden_until_it_is_spent(page: Page):
    """Blurred, not withheld.

    The words are in the DOM so the card reads as "there IS something
    here" - but a CSS filter leaves nothing legible to lift out of the
    markup without paying for it.
    """
    challenge = ChallengePage(page, *FIRST).open()

    expect(challenge.hints).not_to_have_count(0)
    assert challenge.hint_blur(0).startswith("blur("), "a locked hint is not blurred"
    assert challenge.hints_spent_label() == "none spent"


def test_spending_a_hint_reveals_it_and_counts_it(page: Page):
    challenge = ChallengePage(page, *FIRST).open()
    challenge.spend_hint(0)

    # Waiting for the CLASS is not enough - it flips instantly while the
    # blur is a .18s transition. Poll the thing being asserted.
    challenge.wait_for_hint_revealed(0)
    assert challenge.hint_blur(0) == "none"
    assert challenge.hints_spent_label() == "1 of 3 spent"

    # Spent is not a control any more, so it leaves the tab order.
    expect(challenge.hints.first).to_be_disabled()


def test_a_spent_hint_stays_spent_across_a_reload(page: Page):
    challenge = ChallengePage(page, *FIRST).open()
    challenge.spend_hint(0)

    page.reload()
    expect(challenge.hints.first).to_have_class("hint spent")
    assert challenge.hints_spent_label() == "1 of 3 spent"


# --------------------------------------------------------------------------
# The accent picker - no Python needed
# --------------------------------------------------------------------------

def test_the_accent_can_be_changed_and_is_remembered(page: Page):
    quest_map = MapPage(page).open()

    # Mint is the stylesheet's own palette, so it carries no attribute.
    assert quest_map.accent() is None

    quest_map.choose_accent("azure")
    assert quest_map.accent() == "azure"

    page.reload()
    expect(quest_map.board).to_be_visible()
    assert quest_map.accent() == "azure"


@pytest.mark.parametrize("accent", ["mint", "amber", "azure", "violet", "rose"])
def test_every_accent_stays_readable_in_both_themes(page: Page, accent: str):
    """The point of a curated list rather than a colour wheel.

    Each scheme is a PAIR - the road, and the detour off it - and both
    have to hold up on warm cream and on green-black. This checks the
    two that would actually hurt: the accent against the page, and the
    ink on a primary button against its own fill.
    """
    quest_map = MapPage(page).open()
    quest_map.choose_accent(accent)

    for wanted in ["dark", "light"]:
        if quest_map.theme() != wanted:
            quest_map.theme_button.click()
        # Re-selected because flipping the theme re-renders the header.
        quest_map.choose_accent(accent)

        ratios = page.evaluate(
            """() => {
                 const lum = (colour) => {
                   const [r, g, b] = colour.match(/[\\d.]+/g).slice(0, 3).map(Number);
                   const f = (c) => { c /= 255;
                     return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
                   return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
                 };
                 const ratio = (a, b) => {
                   const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
                   return (x + 0.05) / (y + 0.05);
                 };
                 // A probe, because getPropertyValue('--quest') returns
                 // the raw hex as authored; painting it on an element
                 // makes the browser resolve it to rgb() for us.
                 const probe = document.createElement('span');
                 probe.style.color = 'var(--quest)';
                 document.body.appendChild(probe);
                 const accent = getComputedStyle(probe).color;
                 probe.remove();

                 const body = getComputedStyle(document.body).backgroundColor;
                 const button = document.querySelector('.intro-actions .btn.primary');
                 const bs = getComputedStyle(button);
                 return {
                   accentOnPage: ratio(accent, body),
                   inkOnButton: ratio(bs.color, bs.backgroundColor)
                 };
               }"""
        )
        assert ratios["accentOnPage"] >= 3.0, (
            f"{accent}/{wanted}: accent only {ratios['accentOnPage']:.2f}:1 on the page"
        )
        assert ratios["inkOnButton"] >= 4.5, (
            f"{accent}/{wanted}: button text only {ratios['inkOnButton']:.2f}:1 on its fill"
        )


# --------------------------------------------------------------------------
# The banner - these run real Python
# --------------------------------------------------------------------------

@pytest.mark.slow
def test_a_pass_puts_the_way_onward_at_the_top(page: Page, python_runtime_available):
    """The whole reason the banner exists."""
    del python_runtime_available
    challenge = ChallengePage(page, *FIRST).open()
    challenge.write(CORRECT).run()

    expect(challenge.banner).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(challenge.banner).to_have_attribute("data-state", "pass")
    expect(challenge.banner_headline).to_contain_text("Cleared")
    expect(challenge.banner_xp).to_contain_text("XP")

    # Named, and pointing at the actual next challenge - not "continue".
    onward = challenge.banner_action
    expect(onward).to_contain_text("Next:")
    assert "/zone/base-camp/" in onward.get_attribute("href")


@pytest.mark.slow
def test_a_rubric_block_reads_as_review_not_failure(page: Page, python_runtime_available):
    """Warm, not red: the code never ran, a reviewer stopped it.

    Calling that a failure would teach the wrong thing - the test is not
    broken, the approach is.
    """
    del python_runtime_available
    challenge = ChallengePage(page, *FIRST).open()
    challenge.write(WITH_A_SLEEP).run()

    expect(challenge.banner).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(challenge.banner).to_have_attribute("data-state", "review")
    expect(challenge.banner_headline).to_contain_text("Not yet")
    expect(challenge.banner_action).to_contain_text("Fix & run again")


@pytest.mark.slow
def test_a_failing_run_says_why_in_one_line(page: Page, python_runtime_available):
    del python_runtime_available
    challenge = ChallengePage(page, *FIRST).open()
    challenge.write(WRONG_TITLE).run()

    expect(challenge.banner).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(challenge.banner).to_have_attribute("data-state", "fail")
    expect(challenge.banner_headline).to_contain_text("ran and failed")


@pytest.mark.slow
def test_fix_and_run_again_reruns_from_the_banner(page: Page, python_runtime_available):
    """A failed attempt should be one click from another go."""
    del python_runtime_available
    challenge = ChallengePage(page, *FIRST).open()
    challenge.write(WRONG_TITLE).run()
    expect(challenge.banner).to_have_attribute("data-state", "fail",
                                               timeout=RUN_TIMEOUT_MS)

    challenge.write(CORRECT)
    challenge.banner_action.click()
    expect(challenge.banner).to_have_attribute("data-state", "pass",
                                               timeout=RUN_TIMEOUT_MS)
