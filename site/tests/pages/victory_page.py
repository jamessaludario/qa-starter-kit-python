"""
pages/victory_page.py
=====================
The zone-cleared screen, and the profile.

They share a vocabulary - stat tiles, panels, badge cards - so they
share a file rather than repeating the same locators twice.
"""

from pages.base_page import BasePage


class VictoryPage(BasePage):

    def __init__(self, page, zone_id: str):
        super().__init__(page)
        self.zone_id = zone_id
        self.route = "/cleared/" + zone_id

    @property
    def eyebrow(self):
        return self.page.locator(".victory-card .eyebrow")

    @property
    def title(self):
        """The badge name once earned; a plain refusal when it is not."""
        return self.page.get_by_role("heading", level=1)

    @property
    def crest(self):
        """The dashed medallion carrying the zone's two-letter mark."""
        return self.page.locator(".victory-crest")

    def stat(self, label: str):
        """The number above a given caption - "7/7" above "challenges"."""
        return self.page.locator(".stat-tile").filter(
            has=self.page.get_by_text(label, exact=True)
        ).locator("strong")

    def zone_xp(self) -> int:
        return int(self.stat("zone XP").inner_text().replace("+", "").replace(",", ""))

    @property
    def skills(self):
        """"What you can do now" - the zone's objectives, in the past tense."""
        return self.page.locator(".skill-list li")

    @property
    def next_up(self):
        return self.page.locator(".victory-next")

    @property
    def enter_next(self):
        return self.page.locator(".victory-actions .btn.primary")


class ProfilePage(BasePage):
    route = "/progress"

    @property
    def level_name(self):
        return self.page.locator(".profile-head h1")

    def stat(self, label: str):
        return self.page.locator(".stat-tile").filter(
            has=self.page.get_by_text(label, exact=True)
        ).locator("strong")

    def habit(self, label: str):
        return self.page.locator(".habit-list li").filter(
            has=self.page.get_by_text(label, exact=True)
        )

    @property
    def zone_rows(self):
        return self.page.locator(".zone-bars li")

    def zone_row(self, title: str):
        return self.zone_rows.filter(
            has=self.page.locator(".zone-bar-name").get_by_text(title, exact=True)
        )

    @property
    def badges(self):
        return self.page.locator(".badge-card")

    @property
    def export_button(self):
        return self.page.get_by_role("button", name="Export my progress")
