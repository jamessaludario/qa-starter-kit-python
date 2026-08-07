"""
pages/map_page.py
=================
The quest map - the site's home screen.

The map is an ordered list that CSS lifts onto a drawn path, which is
what makes it testable at all: an SVG full of <text> would have no roles,
no links and nothing to tab to.

A zone renders as one of two things, and the difference IS the feature:

    unlocked -> <a class="zone-node ...">   you can click it
    locked   -> <div class="zone-node locked" aria-disabled="true">

So "is this zone locked?" is not a class-name detail we are peeking at -
it is the question of whether the thing is a link.
"""

from pages.base_page import BasePage


class MapPage(BasePage):
    route = "/"

    # ------------------------------------------------------------------
    # Zones
    # ------------------------------------------------------------------

    @property
    def zones(self):
        """Every zone node on the map, locked or not."""
        return self.page.locator(".quest-map .zone-node")

    def zone(self, title: str):
        """One zone, addressed the way a learner sees it: by its title.

        Note the `has=` rather than the more obvious `has_text=`. A
        locked zone's status line names its prerequisite - "Clear The
        Locator Forest first." - so has_text="The Locator Forest" also
        matches Assertion Ridge, and you get a strict-mode violation
        from the very lesson this site teaches in Zone 1.

        Matching on the TITLE element, exactly, asks the question we
        actually meant: which node IS this zone, not which node
        mentions it.
        """
        return self.page.locator(".quest-map .zone-item").filter(
            has=self.page.locator(".zone-title").get_by_text(title, exact=True)
        )

    def zone_link(self, title: str):
        """The clickable form of a zone. Absent when the zone is locked."""
        return self.zone(title).locator("a.zone-node")

    def locked_zone(self, title: str):
        """The non-clickable form. Absent when the zone is open."""
        return self.zone(title).locator(".zone-node.locked")

    def zone_status(self, title: str):
        """The short line under the title: "Cleared", "Locked", "3 of 6 done".

        Deliberately short. Out on the trail there is no room for a full
        sentence - see lock_reason() for the long version.
        """
        return self.zone(title).locator(".zone-state")

    def lock_reason(self, title: str):
        """Which zone opens this one.

        Present in the markup for every locked zone, but only DISPLAYED
        in the stacked layout: on the trail it would wrap across the
        neighbouring zone's name. On wide screens read it from the
        tooltip instead - see lock_tooltip().
        """
        return self.zone(title).locator(".zone-why")

    def lock_tooltip(self, title: str) -> str:
        return self.locked_zone(title).get_attribute("title") or ""

    def zone_shape(self, title: str):
        """The node itself. Its classes carry circle / diamond / square."""
        return self.zone(title).locator(".zone-dot")

    def open_zone(self, title: str):
        self.zone_link(title).click()

    # ------------------------------------------------------------------
    # The running totals
    # ------------------------------------------------------------------

    @property
    def summary(self):
        """"3 challenges cleared of 19 - 90 XP - Intern"."""
        return self.page.locator(".map-stats")

    @property
    def legend(self):
        return self.page.locator(".map-legend")

    # ------------------------------------------------------------------
    # "What do I do now?"
    # ------------------------------------------------------------------

    @property
    def continue_button(self):
        """The primary call to action: "Start ..." or "Continue ...".

        The single most important control on the page - it is the answer
        to the question a returning learner actually has.
        """
        return self.page.locator(".intro-actions .btn.primary")

    @property
    def status_cards(self):
        """Up next / Daily run / Chasing."""
        return self.page.locator(".status-card")

    # ------------------------------------------------------------------
    # Scenery
    # ------------------------------------------------------------------

    @property
    def terrain_select(self):
        """The ground picker, beside "Trophy case"."""
        return self.page.get_by_label("Terrain")

    @property
    def board(self):
        return self.page.locator(".map-board")

    def terrain(self) -> str:
        """Which ground is showing, read off the board's data attribute."""
        return self.board.get_attribute("data-terrain")

    def choose_terrain(self, value: str):
        self.terrain_select.select_option(value)
        return self

    @property
    def accent_select(self):
        """The accent scheme picker, in the header beside the theme toggle."""
        return self.page.get_by_label("Accent")

    def accent(self):
        """Which scheme is applied. None means mint - the stylesheet's
        own palette, which deliberately carries no attribute."""
        return self.page.locator("html").get_attribute("data-accent")

    def choose_accent(self, value: str):
        self.accent_select.select_option(value)
        return self

    @property
    def terrain_layers(self):
        """Every ground, all of which live in the DOM at once."""
        return self.page.locator(".terrain-layer")

    def status_card(self, kind: str):
        return self.status_cards.filter(
            has=self.page.locator(".card-kind").get_by_text(kind, exact=True)
        )
