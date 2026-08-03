"""
pages/base_page.py
==================
What every page of the quest site has: the header (brand, XP, level,
navigation) and the way to open a route.

Routing is hash-based - "#/zone/base-camp/first-test" - because the site
is served as a folder of static files with no server to rewrite paths.
That is why open() builds a URL with a "#" in it rather than a path.
"""

from playwright.sync_api import Page


class BasePage:
    # Child classes override this with the hash route of "their" page.
    route = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, route: str | None = None):
        """Open this page and wait until the app has actually drawn.

        The app renders on load rather than shipping server-side HTML,
        so "the navigation finished" and "the page is usable" are two
        different moments. Waiting for the header is the cheap, honest
        way to mean the second one.
        """
        self.page.goto("/#" + (self.route if route is None else route))
        self.header.wait_for()
        return self

    # ------------------------------------------------------------------
    # The header (present on every page)
    # ------------------------------------------------------------------

    @property
    def header(self):
        return self.page.locator(".site-header")

    @property
    def xp_readout(self):
        """"1,180 / 1,600" in the top right, or "2,400 XP" at the top level."""
        return self.page.locator(".hud-xp")

    @property
    def level_title(self):
        """"Intern", "Junior Tester", ... - the level name beside the XP."""
        return self.page.locator(".hud-title")

    @property
    def level_badge(self):
        """The "LV 4" chip."""
        return self.page.locator(".hud-level")

    @property
    def theme_button(self):
        return self.page.locator(".theme-toggle")

    def xp(self) -> int:
        """The XP as a number, so a test can say `> 0` and mean it.

        The readout is "1,180 / 1,600", so take the part before the
        slash and drop the grouping commas.
        """
        earned = self.xp_readout.inner_text().split("/")[0]
        return int(earned.replace(",", "").replace("XP", "").strip())

    def theme(self) -> str:
        """Which palette is actually applied, read off <html>."""
        return self.page.locator("html").get_attribute("data-theme")

    def go_to_badges(self):
        self.page.get_by_role("link", name="Trophies").click()

    def go_to_progress(self):
        self.page.get_by_role("link", name="Profile").click()

    def go_to_map(self):
        """The brand in the top left is the way home."""
        self.page.locator(".brand").click()
