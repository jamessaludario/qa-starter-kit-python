"""
Nothing may overlap anything else.

The challenge screen is three columns, and the middle one holds whatever
a content author put in a brief - including real Playwright failure
messages, which are long, unbreakable and exactly the thing that bursts
a layout. When that happens the quiz cards slide under the shop panel
and the page looks broken.

The bug this suite was written for: a <fieldset> defaults to
`min-width: min-content`, so it REFUSES to shrink below its widest
child. Give one a call log to hold and it forces itself ~100px past its
column. Every other element shrinks and lets its <pre> scroll; a
fieldset will not until it is told `min-width: 0`.

The check below distinguishes SPILLING from being CLIPPED, which is the
distinction that matters: a <code> inside a scrolling <pre> is wider
than its column by design and is not a bug. Only unclipped overflow is.
"""

import pytest
from pages.challenge_page import ChallengePage
from playwright.sync_api import Page, expect

# One of each challenge kind that renders differently, plus the two
# quizzes whose samples are long enough to have caused this.
CHALLENGES = [
    ("base-camp", "read-the-failure"),        # quiz, long call logs
    ("base-camp", "what-pytest-collects"),    # quiz, short samples
    ("base-camp", "first-test"),              # write-the-test, editor
    ("locator-forest", "meet-get-by-role"),   # locator-match, one input
    ("locator-forest", "strict-mode"),        # fix-the-broken-test
    ("assertion-ridge", "boss-search-end-to-end"),  # boss, long brief
]

# Anything that escapes its column without being clipped by a scroller.
SPILLS = """
(selector) => {
  const column = document.querySelector(selector);
  if (!column) return ['no ' + selector];
  const limit = column.getBoundingClientRect().right;

  // Is some ancestor already clipping this element? A <code> inside a
  // scrolling <pre> is wider than the column on purpose.
  const clipped = (el) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const overflow = getComputedStyle(n).overflowX;
      if (overflow === 'auto' || overflow === 'scroll' || overflow === 'hidden') {
        return n.getBoundingClientRect().right <= limit + 1;
      }
    }
    return false;
  };

  const out = [];
  column.querySelectorAll('*').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (!r.width || r.right <= limit + 1) return;
    if (clipped(el)) return;
    out.push(el.tagName.toLowerCase() + '.' + (el.className || '?')
             + ' +' + Math.round(r.right - limit) + 'px');
  });
  return out;
}
"""


@pytest.mark.parametrize("zone_id, challenge_id", CHALLENGES)
def test_nothing_escapes_the_challenge_columns(page: Page, zone_id, challenge_id):
    page.set_viewport_size({"width": 1600, "height": 1000})
    ChallengePage(page, zone_id, challenge_id).open()
    expect(page.locator(".challenge-layout")).to_be_visible()

    for column in [".challenge-work", ".challenge-rail", ".challenge-side"]:
        spills = page.evaluate(SPILLS, column)
        assert not spills, (
            f"{zone_id}/{challenge_id}: {column} is overlapped by {spills[:4]}"
        )


@pytest.mark.parametrize("zone_id, challenge_id", CHALLENGES)
def test_a_challenge_never_scrolls_sideways(page: Page, zone_id, challenge_id):
    """A horizontal scrollbar is how a layout says it burst.

    Checked at three widths, because the three columns collapse to two
    and then to one, and each of those handovers is a chance to break.
    """
    for width in [1600, 1200, 700]:
        page.set_viewport_size({"width": width, "height": 1000})
        ChallengePage(page, zone_id, challenge_id).open()
        expect(page.locator(".challenge-layout")).to_be_visible()

        overflow = page.evaluate(
            "() => document.documentElement.scrollWidth"
            " - document.documentElement.clientWidth"
        )
        assert overflow <= 1, (
            f"{zone_id}/{challenge_id} at {width}px scrolls sideways by {overflow}px"
        )


# Text wider than its box paints OUTSIDE that box, and the bounding
# rect does not move an inch - so the overlap check above cannot see it.
# It has to be asked about scrollWidth instead. This is how a hint
# quoting expect(page).to_have_url("https://...") - one token, nothing
# to break at - escaped a 300px card while every box measured fine.
BLEED = """
() => {
  const out = [];
  document.querySelectorAll('.challenge-rail *, .banner-words *').forEach((el) => {
    if (!el.textContent.trim()) return;
    const over = el.scrollWidth - el.clientWidth;
    // overflow:visible means nothing is clipping it, so it really is
    // painted outside. A scroller is doing its job and is fine.
    if (over > 1 && getComputedStyle(el).overflowX === 'visible') {
      out.push((el.tagName.toLowerCase() + '.' + (el.className || '?')).slice(0, 40)
               + ' +' + over + 'px');
    }
  });
  return out;
}
"""

# The hints that quote code, which is where unbreakable tokens live.
CODE_HINTS = [
    ("base-camp", "follow-the-menu"),
    ("base-camp", "first-test"),
    ("locator-forest", "scope-the-search"),
    ("assertion-ridge", "boss-search-end-to-end"),
]


@pytest.mark.parametrize("zone_id, challenge_id", CODE_HINTS)
def test_rail_text_wraps_instead_of_painting_outside_its_card(
    page: Page, zone_id, challenge_id
):
    """Hints quote code, and code has no spaces to break at.

    Checked both locked and spent: a blurred hint is still laid out, so
    it can bleed just as far - it is simply harder to notice.
    """
    page.set_viewport_size({"width": 1600, "height": 1000})
    challenge = ChallengePage(page, zone_id, challenge_id).open()
    expect(page.locator(".challenge-rail")).to_be_visible()

    assert not page.evaluate(BLEED), (
        f"{zone_id}/{challenge_id}: text bleeds out while locked: "
        f"{page.evaluate(BLEED)[:4]}"
    )

    for index in range(challenge.hints.count()):
        challenge.hints.nth(index).click()
    if challenge.hints.count():
        challenge.wait_for_hint_revealed(0)

    assert not page.evaluate(BLEED), (
        f"{zone_id}/{challenge_id}: text bleeds out once spent: "
        f"{page.evaluate(BLEED)[:4]}"
    )


def test_a_long_failure_message_scrolls_rather_than_stretching(page: Page):
    """The sample is a REAL error message, so it must not be re-wrapped -
    its line breaks carry meaning. It scrolls inside its own box."""
    page.set_viewport_size({"width": 1600, "height": 1000})
    ChallengePage(page, "base-camp", "read-the-failure").open()

    samples = page.locator(".sample")
    expect(samples).not_to_have_count(0)

    for index in range(samples.count()):
        style = samples.nth(index).evaluate(
            "el => getComputedStyle(el).overflowX + '|' + getComputedStyle(el).whiteSpace"
        )
        overflow, whitespace = style.split("|")
        assert overflow in ("auto", "scroll"), f"sample {index} does not scroll"
        assert whitespace.startswith("pre"), f"sample {index} re-wraps the message"
