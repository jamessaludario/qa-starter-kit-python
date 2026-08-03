"""playwright_lite - a browser-sized subset of the Playwright sync API.

Learner code never imports this name. It imports
`from playwright.sync_api import Page, expect`, exactly as the kit's own
tests do; learner_env/playwright/ re-exports what is in here so a
solution written on the quest site is copy-pasteable into learn/.
"""

from playwright_lite import _runtime
from playwright_lite.sync_api import Error, Locator, Page, TimeoutError, expect

__all__ = ["Error", "Locator", "Page", "TimeoutError", "_runtime", "expect"]
