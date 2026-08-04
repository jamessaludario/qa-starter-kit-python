"""
Running a challenge for real: Pyodide, the shim, the rubric, the grader.

Every test here boots an 11 MB Python runtime in a real browser and runs
real Python against a real DOM. That is slow, and it is the only way to
prove the claim the whole site rests on - that the learner's code is
EXECUTED, not pattern-matched.

What is proved:

    * a correct solution passes and pays XP
    * a wrong one fails with a message worth reading
    * a time.sleep() solution is refused BEFORE it runs
    * a solution that runs but does the wrong thing fails on the checks
    * a different-but-correct locator still passes
    * progress earned this way is still there after a reload

Skip them while iterating on the fast half:

    python -m pytest site/tests/ -m "not slow"
"""

import pytest
from helpers.progress import passed_challenge_count
from pages.challenge_page import RUN_TIMEOUT_MS, ChallengePage
from pages.map_page import MapPage
from pages.zone_page import ZonePage
from playwright.sync_api import Page, expect

# Base Camp, challenge 1: assert the page title. The smallest complete
# test there is, which makes it the right one to prove the machinery on.
FIRST_TEST = "base-camp", "first-test"

CORRECT = '''from playwright.sync_api import Page, expect


def test_home_page_has_the_right_title(page: Page):
    page.goto("https://automationexercise.com/")
    expect(page).to_have_title("Automation Exercise")
'''

WRONG_TITLE = '''from playwright.sync_api import Page, expect


def test_home_page_has_the_right_title(page: Page):
    page.goto("https://automationexercise.com/")
    expect(page).to_have_title("Welcome to the Shop")
'''

WITH_A_SLEEP = '''import time

from playwright.sync_api import Page, expect


def test_home_page_has_the_right_title(page: Page):
    page.goto("https://automationexercise.com/")
    time.sleep(2)
    expect(page).to_have_title("Automation Exercise")
'''

# Parses, runs, asserts something true - and answers a different
# question than the one that was asked. The rubric has no complaint;
# only the behavioural checks can catch this.
RIGHT_SHAPE_WRONG_BEHAVIOUR = '''from playwright.sync_api import Page, expect


def test_home_page_has_the_right_title(page: Page):
    page.goto("https://automationexercise.com/products")
    expect(page.get_by_role("heading", name="All Products")).to_be_visible()
'''

pytestmark = pytest.mark.slow


@pytest.fixture
def first_challenge(page: Page, python_runtime_available) -> ChallengePage:
    """Base Camp's first challenge, open and ready to run."""
    del python_runtime_available
    return ChallengePage(page, *FIRST_TEST).open()


# --------------------------------------------------------------------------
# The happy path
# --------------------------------------------------------------------------

def test_a_correct_solution_passes_and_pays_xp(first_challenge: ChallengePage):
    first_challenge.write(CORRECT).run()

    expect(first_challenge.success).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(first_challenge.success).to_contain_text("Cleared")

    # Not a bare pass: the site itemises what the XP was for. First try
    # and a clean review both pay, so this is worth more than the base.
    expect(first_challenge.xp_awarded).to_be_visible()
    assert first_challenge.xp() > 0

    # Every declared check ran and agreed.
    expect(first_challenge.failed_checks).to_have_count(0)
    expect(first_challenge.checks).not_to_have_count(0)


def test_a_correct_solution_leaves_no_review_notes(first_challenge: ChallengePage):
    first_challenge.write(CORRECT).run()
    expect(first_challenge.success).to_be_visible(timeout=RUN_TIMEOUT_MS)

    # A clean solution earns silence from the reviewer - which is what
    # makes the clean-run bonus mean anything.
    expect(first_challenge.blocking_findings).to_have_count(0)
    expect(first_challenge.advisory_findings).to_have_count(0)


# --------------------------------------------------------------------------
# Failing usefully
# --------------------------------------------------------------------------

def test_a_wrong_solution_fails_with_a_message_worth_reading(
    first_challenge: ChallengePage,
):
    first_challenge.write(WRONG_TITLE).run()

    expect(first_challenge.failure).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(first_challenge.success).to_have_count(0)

    # The point of this test. A red X teaches nothing, so the failure
    # has to carry the three things a real Playwright failure carries:
    # what was expected, what was actually there, and the call log.
    output = first_challenge.crash_output
    expect(output).to_contain_text("Welcome to the Shop")
    expect(output).to_contain_text("Actual value: Automation Exercise")
    expect(output).to_contain_text("Call log:")


def test_a_solution_that_runs_but_does_the_wrong_thing_fails_the_checks(
    first_challenge: ChallengePage,
):
    first_challenge.write(RIGHT_SHAPE_WRONG_BEHAVIOUR).run()

    # It parses, the reviewer approves it, and it even passes its own
    # assertion. Grading on behaviour is what catches it anyway.
    expect(first_challenge.failed_checks.first).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(first_challenge.success).to_have_count(0)

    # And the failed check coaches rather than just reporting red.
    expect(first_challenge.check_feedback.first).to_be_visible()


# --------------------------------------------------------------------------
# The rubric
# --------------------------------------------------------------------------

def test_a_time_sleep_solution_is_refused_before_it_runs(
    first_challenge: ChallengePage,
):
    first_challenge.write(WITH_A_SLEEP).run()

    expect(first_challenge.review).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(first_challenge.review).to_contain_text("Code review: not yet")
    expect(first_challenge.blocking_findings).to_have_count(1)

    # The finding has to explain itself. "No time.sleep" without the
    # reason teaches obedience, not testing.
    finding = first_challenge.blocking_findings.first
    expect(finding).to_contain_text("Change requested")
    expect(finding).to_contain_text("expect()")

    # It stopped BEFORE running: no verdict, and no checks were
    # evaluated. A reviewer would have stopped there too.
    expect(first_challenge.success).to_have_count(0)
    expect(first_challenge.checks).to_have_count(0)

    # The sleep would otherwise have frozen the tab, so the fact that
    # this assertion is reachable at all is part of the proof.
    assert passed_challenge_count(first_challenge.page) == 0


# --------------------------------------------------------------------------
# Grading on behaviour, not on our answer
# --------------------------------------------------------------------------

def test_a_locator_challenge_accepts_the_learners_own_wording(
    page: Page, python_runtime_available
):
    """The Locator Forest's first challenge, solved with a role locator.

    Proves the other challenge kind (a one-line locator box) and the
    check that grades WHICH KIND of locator was used - which is read off
    the action log, never off the learner's source text.
    """
    del python_runtime_available
    challenge = ChallengePage(page, "locator-forest", "meet-get-by-role").open()

    challenge.write_locator('get_by_role("link", name="Products")')
    challenge.run()

    expect(challenge.success).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(challenge.failed_checks).to_have_count(0)


def test_a_locator_challenge_reports_an_over_matching_locator(
    page: Page, python_runtime_available
):
    """The substring trap this challenge's reveal warns about.

    name="Cart" also matches every "Add to cart" link, which is real
    Playwright behaviour rather than a quirk of the shop. The learner
    should see the true count, not a vague refusal.
    """
    del python_runtime_available
    challenge = ChallengePage(page, "locator-forest", "meet-get-by-role").open()

    challenge.write_locator('get_by_role("link", name="Cart")')
    challenge.run()

    expect(challenge.failure).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(challenge.crash_output).to_contain_text("Actual value: 7")


# --------------------------------------------------------------------------
# The whole loop
# --------------------------------------------------------------------------

def test_xp_earned_by_solving_survives_closing_the_page(
    first_challenge: ChallengePage, page: Page
):
    """The definition of done, end to end.

    Write real Playwright, watch it drive a real DOM, earn XP, leave,
    come back, and find it still there.
    """
    first_challenge.write(CORRECT).run()
    expect(first_challenge.success).to_be_visible(timeout=RUN_TIMEOUT_MS)
    earned = first_challenge.xp()

    quest_map = MapPage(page).open()
    page.reload()

    assert quest_map.xp() == earned
    expect(quest_map.summary).to_contain_text("1 challenge cleared")
    expect(quest_map.zone_status("Base Camp")).to_have_text("1 of 6 done")

    # And the zone remembers WHICH one, not just how many.
    base_camp = ZonePage(page, "base-camp").open()
    expect(base_camp.is_cleared("Your first test")).to_have_count(1)
    assert passed_challenge_count(page) == 1
