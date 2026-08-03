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

import pytest
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


@pytest.mark.parametrize("width", [1100, 1280, 1600])
def test_no_two_zone_cards_sit_on_top_of_each_other(page: Page, width: int):
    """The map has to be readable, not just correct.

    Zone positions are hand-authored percentages, so adding a zone can
    push two cards into the same space - which is exactly what happened
    when zones 3 to 11 were added to a map laid out for three. The build
    now refuses that, and this proves it in a real browser where the
    card's actual rendered height is known rather than estimated.

    1100 is the width the map first appears at, and therefore the
    tightest one. Below it the layout falls back to a stacked list.
    """
    page.set_viewport_size({"width": width, "height": 1000})
    quest_map = MapPage(page).open()
    count = quest_map.zones.count()

    boxes = [quest_map.zones.nth(i).bounding_box() for i in range(count)]
    assert all(boxes), "A zone card rendered with no box at all"

    overlapping = []
    for i in range(count):
        for j in range(i + 1, count):
            a, b = boxes[i], boxes[j]
            apart = (
                a["x"] + a["width"] <= b["x"]
                or b["x"] + b["width"] <= a["x"]
                or a["y"] + a["height"] <= b["y"]
                or b["y"] + b["height"] <= a["y"]
            )
            if not apart:
                overlapping.append(
                    f"{quest_map.zones.nth(i).inner_text().splitlines()[0]!r} and "
                    f"{quest_map.zones.nth(j).inner_text().splitlines()[0]!r}"
                )

    assert not overlapping, "Zone cards overlap on the map: " + "; ".join(overlapping)


def test_the_map_becomes_a_readable_list_on_a_phone(page: Page):
    """At 320 px the drawn trail is dropped for a plain stacked list.

    A map you have to pinch and pan is a map half the learners give up
    on, so the wide-screen positioning is the enhancement and the list
    is the base.
    """
    page.set_viewport_size({"width": 320, "height": 720})
    quest_map = MapPage(page).open()

    expect(quest_map.zones).to_have_count(12)

    first = quest_map.zones.nth(0).bounding_box()
    second = quest_map.zones.nth(1).bounding_box()

    # Stacked, not scattered: each card starts below the one before it,
    # and none of them runs off the side of the screen.
    assert second["y"] >= first["y"] + first["height"]
    assert first["x"] + first["width"] <= 320


def test_base_camp_is_open_to_a_learner_who_has_done_nothing(page: Page):
    quest_map = MapPage(page).open()

    # The whole no-account premise rests on this: arrive, start playing.
    expect(quest_map.zone_link("Base Camp")).to_be_visible()
    expect(quest_map.zone_status("Base Camp")).to_have_text("6 challenges")


def test_a_first_time_learner_is_told_exactly_where_to_start(page: Page):
    """Eleven of twelve zones are locked on day one.

    So the map must answer "where do I begin?" without making anyone
    hunt for the one bright node among the dim ones.
    """
    quest_map = MapPage(page).open()

    expect(quest_map.continue_button).to_have_text("Start · Base Camp")
    expect(quest_map.continue_button).to_have_attribute(
        "href", "#/zone/base-camp/first-test"
    )

    # And the card says what that first thing actually is.
    expect(quest_map.status_card("Up next")).to_contain_text("Your first test")


def test_a_zone_you_have_not_earned_is_shut_and_says_why(page: Page):
    quest_map = MapPage(page).open()

    # Locked zones render as a <div>, not an <a>. There is nothing to
    # click, which is stronger than a link that looks disabled.
    expect(quest_map.locked_zone("The Locator Forest")).to_be_visible()
    expect(quest_map.zone_link("The Locator Forest")).to_have_count(0)

    # On the trail the state is one word - there is no room for a
    # sentence without landing it on the next zone's name.
    expect(quest_map.zone_status("The Locator Forest")).to_have_text("Locked")

    # But the reason is never lost: it is in the markup for the stacked
    # layout, and in the tooltip out here.
    expect(quest_map.lock_reason("The Locator Forest")).to_have_text(
        "Clear Base Camp first."
    )
    assert quest_map.lock_tooltip("The Locator Forest") == "Clear Base Camp first."


def test_clearing_base_camp_opens_the_locator_forest(page: Page):
    quest_map = MapPage(page).open()
    assert mark_zone_cleared(page, "base-camp") == 6

    expect(quest_map.zone_link("The Locator Forest")).to_be_visible()
    expect(quest_map.locked_zone("The Locator Forest")).to_have_count(0)
    expect(quest_map.zone_status("Base Camp")).to_have_text("Cleared")

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
    expect(quest_map.zone_status("The Form Marshes")).to_have_text("Locked")
    expect(quest_map.lock_reason("The Form Marshes")).to_have_text(
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
    expect(base_camp.progress_line).to_contain_text("0 of 6 cleared")

    # And the lesson ends by pointing at the first thing to do.
    expect(base_camp.call_to_action).to_have_text("Start · Your first test")


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


def test_the_theme_can_be_switched_and_is_remembered(page: Page):
    """A learner reading lessons for an hour gets to choose the palette.

    The site follows the operating system until they say otherwise, and
    then their choice wins - including across a reload, which is the
    part that makes it a preference rather than a party trick.
    """
    quest_map = MapPage(page).open()
    started_as = quest_map.theme()
    assert started_as in ("dark", "light")

    quest_map.theme_button.click()
    flipped = "light" if started_as == "dark" else "dark"
    assert quest_map.theme() == flipped

    page.reload()
    assert quest_map.theme() == flipped, "The theme choice did not survive a reload"


def test_the_header_says_where_you_are(page: Page):
    """A nav that does not mark the current section is decoration."""
    quest_map = MapPage(page).open()
    expect(page.locator('.hud-links a[aria-current="page"]')).to_have_text("Map")

    quest_map.go_to_badges()
    expect(page.locator('.hud-links a[aria-current="page"]')).to_have_text("Trophies")


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
