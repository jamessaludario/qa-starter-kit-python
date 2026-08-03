"""
The quest map: does it render, and does it gate progress honestly?

These tests never boot Python, so they are fast. What they prove is the
promise the map makes to a learner:

    * every zone is on the map, including the ones not built yet
    * a zone you have not earned is genuinely shut, and says why
    * clearing its prerequisite genuinely opens it
    * progress written in one visit is still there in the next

The last one is deliberately checked twice in this suite: cheaply here
with seeded progress, and expensively in test_site_challenge.py with XP
earned by actually solving a challenge. This one catches a broken
storage layer in a second; that one proves the whole loop.
"""

from helpers.progress import mark_zone_cleared, passed_challenge_count
from pages.map_page import MapPage
from pages.zone_page import ZonePage
from playwright.sync_api import Page, expect


def test_the_map_lists_every_zone_in_order(page: Page):
    quest_map = MapPage(page).open()

    # 12 zones: Base Camp through the Runner's Gate, plus the Desktop
    # Outpost side quest and the endgame.
    expect(quest_map.zones).to_have_count(12)

    # The first and last, by name, so a reordering that broke the path
    # would show up here rather than as a strange-looking map.
    expect(quest_map.zones.first).to_contain_text("Base Camp")
    expect(quest_map.zones.last).to_contain_text("Ship It")


def test_base_camp_is_open_to_a_learner_who_has_done_nothing(page: Page):
    quest_map = MapPage(page).open()

    # The whole no-account premise rests on this: arrive, start playing.
    expect(quest_map.zone_link("Base Camp")).to_be_visible()
    expect(quest_map.zone_status("Base Camp")).to_contain_text("0 / 6 cleared")


def test_a_zone_you_have_not_earned_is_shut_and_says_why(page: Page):
    quest_map = MapPage(page).open()

    # Locked zones render as a <div>, not an <a>. There is nothing to
    # click, which is stronger than a link that looks disabled.
    expect(quest_map.locked_zone("The Locator Forest")).to_be_visible()
    expect(quest_map.zone_link("The Locator Forest")).to_have_count(0)

    # And it names the way out rather than just refusing.
    expect(quest_map.zone_status("The Locator Forest")).to_have_text(
        "Clear Base Camp first."
    )


def test_clearing_base_camp_opens_the_locator_forest(page: Page):
    quest_map = MapPage(page).open()
    assert mark_zone_cleared(page, "base-camp") == 6

    expect(quest_map.zone_link("The Locator Forest")).to_be_visible()
    expect(quest_map.locked_zone("The Locator Forest")).to_have_count(0)
    expect(quest_map.zone_status("Base Camp")).to_contain_text("6 / 6 cleared")

    # ...and only the next one. Unlocking must not cascade down the map.
    expect(quest_map.locked_zone("The Form Marshes")).to_be_visible()


def test_an_open_zone_with_no_content_yet_says_coming_soon(page: Page):
    quest_map = MapPage(page).open()

    # The Desktop Outpost is a side quest: it needs no prerequisite, so
    # it is open from the start and has nothing to play yet. A stub is a
    # shipped zone, not a bug - it admits the gap rather than showing a
    # meaningless "0 / 0 cleared".
    expect(quest_map.zone_link("Desktop Outpost")).to_be_visible()
    expect(quest_map.zone_status("Desktop Outpost")).to_have_text("Coming soon")


def test_a_zone_that_is_mapped_but_not_built_shows_its_shape(page: Page):
    quest_map = MapPage(page).open()

    # A stub behind a prerequisite stays shut and names what opens it,
    # exactly like a built zone would.
    expect(quest_map.zone_status("The Form Marshes")).to_have_text(
        "Clear Assertion Ridge first."
    )

    # The zone page is reachable regardless, so the shape of the whole
    # game is visible without pretending the content exists.
    marshes = ZonePage(page, "form-marshes").open()
    expect(marshes.title).to_have_text("The Form Marshes")
    expect(marshes.progress_line).to_contain_text("not built yet")

    # The shape of the zone is still visible: what it will teach, and
    # what it will ask you to do.
    expect(marshes.objectives.first).to_be_visible()
    expect(marshes.planned_challenges).to_have_count(7)


def test_the_desktop_side_quest_is_honest_about_not_running_here(page: Page):
    outpost = ZonePage(page, "desktop-outpost").open()

    # This zone drives native Windows windows through pywinauto. It
    # cannot execute in a browser, and the lesson has to say so on its
    # face rather than let a learner discover it by failing.
    expect(outpost.lesson).to_contain_text("cannot run here")
    expect(outpost.lesson).to_contain_text("python desktop/run_tests.py")


def test_a_zone_page_lists_its_challenges(page: Page):
    base_camp = ZonePage(page, "base-camp").open()

    expect(base_camp.challenges).to_have_count(6)
    expect(base_camp.challenge("Your first test")).to_be_visible()
    expect(base_camp.progress_line).to_contain_text("0 of 6 challenges cleared")


def test_progress_survives_a_reload(page: Page):
    quest_map = MapPage(page).open()
    mark_zone_cleared(page, "base-camp")

    earned = quest_map.xp()
    assert earned > 0, "Seeding Base Camp should have awarded XP"

    page.reload()

    # Same numbers, from storage, after the app was torn down and built
    # again from scratch.
    assert quest_map.xp() == earned
    expect(quest_map.summary).to_contain_text("6 challenges cleared")
    assert passed_challenge_count(page) == 6


def test_erasing_progress_locks_the_map_again(page: Page):
    quest_map = MapPage(page).open()
    mark_zone_cleared(page, "base-camp")
    expect(quest_map.zone_link("The Locator Forest")).to_be_visible()

    # The reset is behind a window.confirm(), which is the one thing a
    # learner should not be able to do by accident.
    page.on("dialog", lambda dialog: dialog.accept())
    quest_map.go_to_progress()
    page.get_by_role("button", name="Erase everything").click()

    quest_map.go_to_map()
    expect(quest_map.locked_zone("The Locator Forest")).to_be_visible()
    assert quest_map.xp() == 0
