"""
The map's ground, and the picker that changes it.

Six grounds behind the same trail. It is the cheapest fun in the
product - a learner looks at this screen more than any other - but it
earns its tests because it makes two claims that are easy to break
later:

  * changing scenery must not disturb the quest. The trail, the zone
    states and the progress are not re-rendered, only revealed, so a
    change of ground cannot restart the road's animation or re-read
    what you have cleared.
  * the choice is a DISPLAY preference and lives in its own storage
    key. It has no business travelling inside a progress export, which
    is the file a learner hands in.
"""

import json

from helpers.progress import STORAGE_KEY, mark_zone_cleared
from pages.map_page import MapPage
from playwright.sync_api import Page, expect

TERRAIN_KEY = "quest-for-automation.terrain"

# Every ground the picker offers. `flat` is the absence of one.
GROUNDS = ["blueprint", "survey", "contours", "terminal", "night", "flat"]


def test_the_map_starts_on_the_blueprint(page: Page):
    """The default is the one ground that says something true.

    Graph paper with the wireframes of a product grid, a form and a
    cart: the quest is through PAGES, not mountains. The other five are
    scenery; this one is the argument.
    """
    quest_map = MapPage(page).open()
    assert quest_map.terrain() == "blueprint"


def test_the_picker_offers_every_ground(page: Page):
    quest_map = MapPage(page).open()
    expect(quest_map.terrain_select).to_be_visible()

    values = quest_map.terrain_select.locator("option").evaluate_all(
        "options => options.map(o => o.value)"
    )
    assert values == GROUNDS


def test_choosing_a_ground_shows_it(page: Page):
    quest_map = MapPage(page).open()

    for ground in GROUNDS:
        quest_map.choose_terrain(ground)
        assert quest_map.terrain() == ground, f"{ground} did not take"


def test_the_ground_survives_a_reload(page: Page):
    quest_map = MapPage(page).open()
    quest_map.choose_terrain("survey")

    page.reload()
    expect(quest_map.board).to_be_visible()
    assert quest_map.terrain() == "survey"


def test_changing_the_ground_does_not_disturb_the_quest(page: Page):
    """Scenery is revealed, not re-rendered.

    All six grounds are in the DOM from the start and a data attribute
    decides which is painted. If this ever became a re-render, the
    road's dash animation would restart on every change and the map
    would re-read progress for nothing.
    """
    quest_map = MapPage(page).open()
    mark_zone_cleared(page, "base-camp")

    before = quest_map.zones.count()
    cleared_before = quest_map.summary.inner_text()
    # The <ol> the zones live in, to prove it is the same element after.
    quest_map.page.evaluate(
        "() => { document.querySelector('.quest-map').dataset.witness = 'same'; }"
    )

    quest_map.choose_terrain("night")

    assert quest_map.zones.count() == before
    assert quest_map.summary.inner_text() == cleared_before
    expect(quest_map.zone_link("The Locator Forest")).to_be_visible()
    # Survived because nothing was rebuilt.
    assert quest_map.page.locator(".quest-map").get_attribute("data-witness") == "same"


def test_the_scenery_choice_stays_out_of_the_progress_export(page: Page):
    """A display preference must not ride along in a handed-in file.

    Progress is exportable so a learner can move machines or a bootcamp
    can collect completions. Which background someone likes is not part
    of that, and putting it there would also mean importing somebody
    else's file changed your scenery.
    """
    quest_map = MapPage(page).open()
    quest_map.choose_terrain("terminal")
    mark_zone_cleared(page, "base-camp")

    saved = page.evaluate("(key) => window.localStorage.getItem(key)", STORAGE_KEY)
    progress = json.loads(saved)
    assert "terrain" not in json.dumps(progress), (
        "The terrain leaked into the progress object: " + saved[:200]
    )

    # It is kept, just kept separately.
    assert page.evaluate("(key) => window.localStorage.getItem(key)", TERRAIN_KEY) \
        == "terminal"


def test_no_ground_paints_a_solid_black_shape(page: Page):
    """An SVG shape with no fill rule is not invisible - it is BLACK.

    That is exactly how the blueprint shipped broken: its wireframes
    were styled through a wrapper class, the terrain switcher lifts them
    into its own layer, the rules stopped matching, and three faint page
    outlines became three black slabs. Nothing in the scenery should
    ever be a solid dark block, on any ground.
    """
    quest_map = MapPage(page).open()

    for ground in GROUNDS:
        quest_map.choose_terrain(ground)
        offenders = page.evaluate(
            """(ground) => {
                 const layer = document.querySelector('.map-board .t-' + ground);
                 if (!layer) return [];
                 return [...layer.querySelectorAll('rect, circle, ellipse, path, polygon')]
                   .filter((el) => {
                     const fill = getComputedStyle(el).fill;
                     // Fully opaque black is the browser's default, and
                     // never a colour this design asks for.
                     return fill === 'rgb(0, 0, 0)';
                   })
                   .map((el) => el.tagName + '.' + (el.getAttribute('class') || '?'));
               }""",
            ground,
        )
        assert not offenders, f"{ground} paints solid black: {offenders[:5]}"


def test_native_controls_follow_the_theme(page: Page):
    """color-scheme, or the terrain drop-down is unreadable in the dark.

    A <select>'s popup is drawn by the OS, not by our CSS, so styling
    <option> does not reliably reach it. Without color-scheme the dark
    theme gets light text on the platform's white popup - which is how
    the picker shipped with an invisible list.
    """
    quest_map = MapPage(page).open()

    for wanted in ["dark", "light"]:
        if quest_map.theme() != wanted:
            quest_map.theme_button.click()
        assert quest_map.theme() == wanted
        scheme = page.evaluate(
            "() => getComputedStyle(document.documentElement).colorScheme"
        )
        assert scheme == wanted, f"theme is {wanted} but color-scheme is {scheme!r}"


def test_the_grounds_are_scenery_to_a_screen_reader(page: Page):
    """Decorative by construction: every layer is aria-hidden.

    A screen reader announcing hatching and star fields between the
    zone names would make the map worse, not more accessible.
    """
    quest_map = MapPage(page).open()
    expect(quest_map.terrain_layers).not_to_have_count(0)

    exposed = quest_map.terrain_layers.evaluate_all(
        "layers => layers.filter(l => l.getAttribute('aria-hidden') !== 'true').length"
    )
    assert exposed == 0, f"{exposed} terrain layer(s) are not aria-hidden"
