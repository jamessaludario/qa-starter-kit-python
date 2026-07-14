"""
Your first test: the app loads.

This "smoke test" proves the whole toolchain works end to end — config,
browser, your app's URL — before you invest in real tests. It should
pass immediately after you fill in .env. Then grow your suite:

  - baseline tests:   every important page loads and shows its key
                      elements (one test file per page)
  - e2e tests:        full user journeys (log in -> do a thing -> verify)
  - regression tests: edge cases and things that once broke

Generate them with the prompts/ folder and your AI agent, or write them
by hand using pages/example_page.py.template as a starting point.
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_app


def test_app_loads(page: Page):
    # Step 1: open the app's front page (BASE_URL from your .env)
    open_app(page)

    # Step 2: the page rendered something — it has a title...
    expect(page).not_to_have_title("")

    # ...and a visible body. Replace these generic checks with something
    # specific to YOUR app (its heading, its logo, its login button).
    expect(page.locator("body")).to_be_visible()
