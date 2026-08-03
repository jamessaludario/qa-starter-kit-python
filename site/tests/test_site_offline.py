"""
The service worker: offline after the first visit, but never stale.

These two properties pull in opposite directions, and getting the
balance wrong is not a cosmetic bug - it is the difference between a
learner seeing today's lesson and seeing last week's forever.

The failure that prompted this suite: index.html was cached cache-first
along with everything else. But index.html is the document that PINS
every asset version (each URL carries ?v=<build id>), so serving it from
cache meant a rebuilt site kept loading the old page, which kept asking
for the old assets. No number of reloads would show new content.

The fix, and what these tests hold in place:

    the page itself  -> network first, cache as a fallback
    everything else  -> cache first

Read from the SERVER side. From inside the page a cache hit and a
network fetch look identical; the only honest witness is whether the
server was asked at all.
"""

from pages.map_page import MapPage
from playwright.sync_api import Page, expect

# The service worker takes over the page asynchronously, some time after
# the first load. Until it does, these tests would be measuring nothing.
CONTROLLED = "navigator.serviceWorker.controller !== null"


def _wait_until_controlled(page: Page):
    page.wait_for_function(CONTROLLED, timeout=20_000)


def test_the_page_itself_is_always_fetched_fresh(page: Page, server_requests):
    """A rebuild must reach the learner on the very next reload."""
    MapPage(page).open()
    _wait_until_controlled(page)

    server_requests.clear()
    page.reload()
    expect(page.locator(".quest-map")).to_be_visible()

    documents = [path for path in server_requests if path in ("/", "/index.html")]
    assert documents, (
        "The page was served from the service worker cache without asking the "
        "server. That is how a rebuilt site keeps showing old content: "
        "index.html pins every asset's ?v=, so a stale document pins stale "
        "assets. Navigations must be network-first."
    )


def test_the_heavy_assets_are_served_from_cache(page: Page, server_requests):
    """The other half of the bargain, and the reason the cache exists.

    If everything went to the network, the 11 MB Python runtime would be
    re-fetched on a train and the lesson would stop.
    """
    MapPage(page).open()
    _wait_until_controlled(page)

    server_requests.clear()
    page.reload()
    expect(page.locator(".quest-map")).to_be_visible()

    # The versioned assets the page pulls in. A new build changes the
    # ?v= and therefore the URL, so a cache hit here can never be stale.
    cached = [path for path in server_requests if path.startswith(("/app.css", "/content.js"))]
    assert not cached, (
        "Versioned assets went back to the network: " + ", ".join(cached) +
        ". They are immutable for a build, so this is pure waste."
    )


def test_the_site_still_works_with_the_network_switched_off(page: Page, context):
    """The whole point of having a service worker at all."""
    quest_map = MapPage(page).open()
    _wait_until_controlled(page)

    context.set_offline(True)
    try:
        page.reload()
        # Not just "something rendered": the content came from cache and
        # the app booted off it.
        expect(quest_map.zones).to_have_count(12)
        expect(quest_map.zone_link("Base Camp")).to_be_visible()
    finally:
        context.set_offline(False)
