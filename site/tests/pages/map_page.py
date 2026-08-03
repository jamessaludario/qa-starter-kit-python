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
        """The line under the title: "2 / 6 cleared", or why it is shut."""
        return self.zone(title).locator(".zone-meta")

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
