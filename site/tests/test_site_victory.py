"""
The zone-cleared screen, and the profile it feeds.

Every other view is about what is still to do. Victory is the one place
the site stops and says what a learner can now do that they could not
before - which is the whole point of having XP and badges at all.

The rule these tests hold: everything on that screen is READ from what
actually happened. If the numbers could be congratulation nobody earned,
the screen is worse than not having one.
"""

import pytest
from helpers.progress import mark_zone_cleared
from pages.map_page import MapPage
from pages.victory_page import ProfilePage, VictoryPage
from pages.zone_page import ZonePage
from playwright.sync_api import Page, expect


def test_a_zone_you_have_not_cleared_does_not_congratulate_you(page: Page):
    """The screen is reachable by typing the URL, so it has to cope."""
    victory = VictoryPage(page, "locator-forest").open()

    expect(victory.title).to_have_text("The Locator Forest is not cleared")
    expect(victory.crest).to_have_count(0)
    expect(page.get_by_role("link", name="Back to The Locator Forest")).to_be_visible()


def test_clearing_a_zone_earns_the_screen(page: Page):
    MapPage(page).open()
    mark_zone_cleared(page, "locator-forest")

    victory = VictoryPage(page, "locator-forest").open()

    # The badge for THIS zone, by name, not a generic "well done".
    expect(victory.eyebrow).to_have_text("Zone cleared")
    expect(victory.title).to_have_text("Pathfinder")
    expect(victory.crest).to_contain_text("LF")


def test_the_numbers_are_the_ones_actually_banked(page: Page):
    MapPage(page).open()
    mark_zone_cleared(page, "locator-forest")
    victory = VictoryPage(page, "locator-forest").open()

    # Seeded as seven challenges passed on the first try with no hints,
    # so the screen must say exactly that and no more.
    expect(victory.stat("challenges")).to_have_text("7/7")
    expect(victory.stat("hints spent")).to_have_text("0")
    assert victory.zone_xp() > 0


def test_it_says_what_you_can_do_now_and_where_to_go_next(page: Page):
    MapPage(page).open()
    mark_zone_cleared(page, "locator-forest")
    victory = VictoryPage(page, "locator-forest").open()

    # The zone's own objectives, which were a promise on the way in.
    expect(victory.skills).to_have_count(5)
    expect(victory.skills.first).to_contain_text("priority order")

    expect(victory.next_up).to_contain_text("Next: Assertion Ridge")
    expect(victory.enter_next).to_have_attribute("href", "#/zone/assertion-ridge")


def test_the_zone_page_offers_the_screen_once_it_is_earned(page: Page):
    MapPage(page).open()
    mark_zone_cleared(page, "locator-forest")

    zone = ZonePage(page, "locator-forest").open()
    expect(zone.call_to_action).to_have_text("See what you earned")
    zone.call_to_action.click()
    expect(VictoryPage(page, "locator-forest").title).to_have_text("Pathfinder")


# --------------------------------------------------------------------------
# Profile
# --------------------------------------------------------------------------

def test_the_profile_reports_real_counters(page: Page):
    MapPage(page).open()
    mark_zone_cleared(page, "base-camp")

    profile = ProfilePage(page).open()

    # The page title and the header both name the level, and they must
    # agree - two readouts of one number that can disagree is a bug.
    expect(profile.level_name).to_have_text(profile.level_title.inner_text())
    expect(profile.stat("total XP")).not_to_have_text("0")
    expect(profile.stat("badges")).to_contain_text("/")

    # Every zone is listed, cleared or not, so "what is left" is one look.
    expect(profile.zone_rows).to_have_count(12)
    expect(profile.zone_row("Base Camp")).to_contain_text("100%")


def test_the_profile_shows_habits_rather_than_invented_skills(page: Page):
    """These four are counters the runner really keeps.

    A radar chart with made-up axes would look better and mean nothing;
    every number here can be traced to something the learner ran.
    """
    profile = ProfilePage(page).open()

    for habit in ["Role-based locators used", "Clean reviews",
                  "First-try passes", "Sleeps caught"]:
        expect(profile.habit(habit)).to_have_count(1)


def test_progress_can_still_be_exported(page: Page):
    """The only way off this machine, since there are no accounts."""
    profile = ProfilePage(page).open()
    with page.expect_download() as download:
        profile.export_button.click()
    assert download.value.suggested_filename == "quest-progress.json"


@pytest.mark.parametrize("width", [1280, 720, 360])
def test_the_profile_survives_a_narrow_window(page: Page, width: int):
    page.set_viewport_size({"width": width, "height": 900})
    profile = ProfilePage(page).open()

    expect(profile.zone_rows).to_have_count(12)
    # Nothing may push the page sideways: a horizontal scrollbar on a
    # phone is how a layout tells you it was only ever tested wide.
    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 1, f"The page scrolls sideways by {overflow}px at {width}px"
