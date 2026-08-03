"""
helpers/progress.py
===================
Reaching a given state of progress without playing the game to get
there.

Why this exists: proving that "clearing Base Camp unlocks the Locator
Forest" should not cost six Pyodide runs. So one test earns XP for real
(that is the point of test_site_challenge.py), and the tests about the
MAP seed the progress store directly and stay fast.

The seeding deliberately reads the site's own content at runtime rather
than hard-coding challenge ids. Add a seventh challenge to Base Camp and
these helpers keep telling the truth; hard-coded ids would quietly start
marking a zone "cleared" that no longer is.
"""

import json

# The key the site's progress store uses. One string, in one place: if
# it ever changes, the site's own tests should be what notices.
STORAGE_KEY = "quest-for-automation.v1"

# Written in the browser, where the content already is. Mirrors what the
# app itself writes when a learner passes a challenge, so the site does
# not have to know it was us.
_MARK_ZONE_CLEARED = """
(zoneId) => {
  const KEY = "quest-for-automation.v1";
  const zone = window.QUEST_CONTENT.zones.find((z) => z.id === zoneId);
  if (!zone) throw new Error("No such zone: " + zoneId);
  if (!zone.challenges.length) throw new Error("Zone has no challenges: " + zoneId);

  const saved = JSON.parse(window.localStorage.getItem(KEY) || "{}");
  saved.version = 1;
  saved.challenges = saved.challenges || {};
  saved.badges = saved.badges || {};
  saved.xp = saved.xp || 0;

  zone.challenges.forEach((challenge) => {
    saved.challenges[zoneId + "/" + challenge.id] = {
      status: "passed", attempts: 1, hints: [], xp: challenge.xp, clean: true
    };
    saved.xp += challenge.xp;
  });

  window.localStorage.setItem(KEY, JSON.stringify(saved));
  return zone.challenges.length;
}
"""


def mark_zone_cleared(page, zone_id: str) -> int:
    """Mark every challenge in a zone as passed, then reload.

    The reload matters: the app reads localStorage once at boot, so
    writing the key without reloading would change the storage and not
    the screen - a test that passes for the wrong reason.

    Returns how many challenges were marked, so a caller can assert the
    zone was not silently empty.
    """
    marked = page.evaluate(_MARK_ZONE_CLEARED, zone_id)
    page.reload()
    return marked


def stored_progress(page) -> dict:
    """Whatever the site has actually saved, as a dict.

    Used to prove persistence is real storage rather than a value the
    page happened to still be holding in memory.
    """
    raw = page.evaluate(
        "(key) => window.localStorage.getItem(key)", STORAGE_KEY
    )
    if not raw:
        return {}
    return json.loads(raw)


def passed_challenge_count(page) -> int:
    """How many challenges the saved progress calls passed."""
    saved = stored_progress(page)
    return len([
        key for key, record in saved.get("challenges", {}).items()
        if record.get("status") == "passed"
    ])
