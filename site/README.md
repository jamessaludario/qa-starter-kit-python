# Quest for Automation

A gamified, browser-based adventure that teaches Playwright + pytest.
Learners read a short lesson, then **write real Python and watch it drive
a real DOM** — earning XP, badges and zone completions on an RPG quest
map.

It is the third track of this kit, alongside the 26 commented practice
tests in `learn/` and the project scaffolder. Think of it as the web
successor to `python tour.py`, which still works and is untouched.

**No backend. No accounts. No server-side execution.** A folder of static
files you can drop on GitHub Pages or Cloudflare Pages.

---

## Run it

```bash
python site/fetch_vendor.py
```

Downloads Pyodide (~12 MB) into the git-ignored `site/vendor/`. Once, on
first setup.

```bash
python site/build_site.py
```

Builds `site/dist/`, serves it on <http://127.0.0.1:8000/>, and opens a
browser. `--no-open` to stay quiet, `--build-only` to just write the
folder.

It needs a real HTTP server — WebAssembly will not load over `file://` —
which is why serving is the default rather than an extra step. Stdlib
only: no `pip install`, no npm, nothing added to `requirements.txt`.

## Test it

```bash
python -m pytest site/tests/
```

The site that teaches Playwright is tested with Playwright, using this
repo's own layering: tests assert, page objects hold every locator.

- `test_shim_unit.py` — the shim against a fake bridge. No browser, no
  Pyodide, milliseconds.
- `test_site_map.py` — the map renders, zones lock and unlock, progress
  survives a reload.
- `test_site_challenge.py` — a correct solution passes, a wrong one
  fails with useful feedback, a `time.sleep` solution is rejected before
  it runs. These boot Python in the browser, so they are marked `slow`.

Skip the slow half while iterating:

```bash
python -m pytest site/tests/ -m "not slow"
```

---

## How it works, in one paragraph

Playwright drives browsers from the outside, so it cannot run inside
one. Three pieces stand in: **AutomationVille**, a static look-alike of
automationexercise.com with the same ids and class names, in a
same-origin iframe; **Pyodide**, real CPython compiled to WebAssembly,
which *executes* the learner's code rather than pattern-matching it; and
**`playwright_lite`**, a Playwright-shaped shim that drives that DOM with
faithful auto-waiting, strict mode, and Playwright's own error messages.
Learners import it as `from playwright.sync_api import Page, expect`, so
a solution written here can be pasted into `tour-tests/` and run against
the real site without changing a character.

The full design — the bridge decision and its trade-offs, the grading
model, the content pipeline, and **what was deliberately not built** — is
in [ARCHITECTURE.md](ARCHITECTURE.md).

## How grading works, in one paragraph

Never by comparing the learner's code to ours. Four independent sources:
the **action log** (what their test actually did to the page), the **app
snapshot** (where the shop ended up), the **live DOM**, and an **AST
rubric** run with Python's `ast` module that enforces this repo's
conventions — no `time.sleep()`, `expect()` where a bare `assert` would
be flaky, locators kept out of tests. Rubric violations produce coaching
feedback in the voice of a senior reviewer, not a red X. Find a better
locator than ours and you pass; paste ours with a sleep bolted on and you
do not.

---

## Content

| # | Zone | Teaches | State |
|---|---|---|---|
| 0 | Base Camp | AAA, pytest collection, your first run | **Built** |
| 1 | The Locator Forest | Locator priority, chaining, strict mode | **Built** |
| 2 | Assertion Ridge | Web-first `expect()`, auto-waiting | **Built** |
| 3 | The Form Marshes | `fill`, `check`, `select_option`, negative cases | Stub |
| 4 | Cart Caverns | Multi-step state, counts, removal | Stub |
| 5 | Fixture Foundry | `conftest.py`, `yield`, fixture scope | Stub |
| 6 | Page Object Peaks | Boss: refactor into `pages/` + `helpers/` | Stub |
| 7 | The Flaky Swamp | Sleeps vs waits, races, retries, debugging | Stub |
| 8 | Checkout Citadel | Full E2E journey, data setup, cleanup | Stub |
| 9 | The Runner's Gate | Markers, smoke vs regression, reports, CI | Stub |
| — | Desktop Outpost | pywinauto, when Playwright cannot reach | Stub, read-only by design |
| ★ | Endgame: Ship It | Scaffold a suite for your own app | Stub |

A **stub** is a real, shipped zone: it appears on the map with its
objectives and planned challenge titles, so the shape of the whole game
is visible. It has no `challenges/` yet, which means it can never be
"cleared", which means zones behind it stay locked. Honest rather than
tidy.

Adding one is a data change, not an engine change — see
[CONTRIBUTING-CONTENT.md](CONTRIBUTING-CONTENT.md). **Adding a challenge
is one JSON file.**

---

## Layout

```
site/
  ARCHITECTURE.md            the bridge decision, grading, what we did not build
  CONTRIBUTING-CONTENT.md    how to add a zone or a challenge
  build_site.py              content/ + src/ -> dist/
  fetch_vendor.py            downloads Pyodide into vendor/
  pytest.ini                 config for the site's OWN suite
  content/                   game.json, about.md, zones/
  src/
    app.css
    index is generated       (build_site.py writes dist/index.html)
    js/                      router, quest map, challenge view, grading, editor
    mockapp/                 AutomationVille — the shop under test
    pylib/                   the Python that runs inside Pyodide
      playwright_lite/       the shim
      learner_env/           what `from playwright.sync_api import ...` resolves to
      quest/                 harness.py (runs an attempt), rubric.py (the AST review)
    sw.js                    offline after the first visit
  tests/                     the site's own Playwright + pytest suite
  vendor/                    Pyodide (git-ignored, ~12 MB)
  dist/                      build output (git-ignored)
```

Both `vendor/` and `dist/` are git-ignored. CI rebuilds `dist/` fresh on
every deploy, and 12 MB of WebAssembly does not belong in a teaching
repo's history.

## Deploying

`site/dist/` is the whole site. Any static host will do.

```bash
python site/fetch_vendor.py
python site/build_site.py --build-only
# publish site/dist/
```

No special headers are required — that was the point of the bridge
decision. Serve it from a subpath if you like; every URL in the app is
relative and routing is hash-based, because GitHub Pages has no server to
rewrite `/zone/locator-forest` back to `index.html`.

## Accessibility and reach

Non-negotiables, and the site's own tests cover the first two:

- **Keyboard accessible** throughout. The editor is a real `<textarea>`;
  Escape-then-Tab leaves it, so it is never a keyboard trap.
- **Readable at 320 px.** The quest map is an ordered list that CSS
  lifts onto a drawn path on wide screens — not an SVG you cannot tab
  through.
- Respects `prefers-reduced-motion`.
- **Works offline** after the first visit.
- **No analytics, no telemetry, nothing uploaded.** Progress lives in
  this browser's local storage; export it from the Progress page to move
  machines.
