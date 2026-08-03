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
        """The "530 XP" in the top right."""
        return self.page.locator(".hud-xp")

    @property
    def level_title(self):
        """"Intern", "Junior Tester", ... - the level name beside the XP."""
        return self.page.locator(".hud-title")

    def xp(self) -> int:
        """The XP as a number, so a test can say `> 0` and mean it."""
        return int(self.xp_readout.inner_text().split()[0])

    def go_to_badges(self):
        self.page.get_by_role("link", name="Badges").click()

    def go_to_progress(self):
        self.page.get_by_role("link", name="Progress").click()

    def go_to_map(self):
        """The brand in the top left is the way home."""
        self.page.locator(".brand").click()
