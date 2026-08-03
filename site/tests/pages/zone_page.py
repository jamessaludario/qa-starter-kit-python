"""
pages/zone_page.py
==================
One zone: its objectives, its lesson, and its list of challenges.

A zone with no challenges yet is not an error state - it is a shipped
stub, and it renders its PLANNED challenge titles instead. Both shapes
are addressed here so a test can assert on either without knowing how
the view decides.
"""

from pages.base_page import BasePage


class ZonePage(BasePage):

    def __init__(self, page, zone_id: str):
        super().__init__(page)
        self.zone_id = zone_id
        self.route = "/zone/" + zone_id

    @property
    def title(self):
        return self.page.get_by_role("heading", level=1)

    @property
    def progress_line(self):
        """The line under the title: what the zone teaches, then how far
        through it you are - or "mapped, not built yet" for a stub."""
        return self.page.locator(".zone-sub")

    @property
    def call_to_action(self):
        """"Start ..." / "Continue ..." at the foot of the lesson."""
        return self.page.locator(".zone-cta .btn")

    @property
    def objectives(self):
        return self.page.locator(".objectives li")

    @property
    def lesson(self):
        return self.page.locator(".lesson")

    # ------------------------------------------------------------------
    # Challenges - built, and merely planned
    # ------------------------------------------------------------------

    @property
    def challenges(self):
        return self.page.locator(".challenge-row")

    def challenge(self, title: str):
        return self.page.locator(".challenge-row").filter(has_text=title)

    def open_challenge(self, title: str):
        self.challenge(title).locator("a.challenge-link").click()

    def is_cleared(self, title: str):
        """A cleared row carries a screen-reader-only "cleared" marker."""
        return self.challenge(title).get_by_text("cleared")

    @property
    def planned_challenges(self):
        """The titles a stub zone lists instead of real challenges."""
        return self.page.locator(".rail-list.stub .planned")
