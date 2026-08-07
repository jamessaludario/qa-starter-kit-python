# Quest for Automation — architecture

How the site runs a learner's Playwright Python in a browser, how it
decides whether they got it right, how content becomes pages, and — the
part that usually goes unwritten — what was deliberately left out.

Read this before changing anything in `src/`. Adding a lesson or a
challenge needs none of it: see [CONTRIBUTING-CONTENT.md](CONTRIBUTING-CONTENT.md).

---

## 1. The problem

Playwright drives browsers **from the outside**. It speaks CDP to a
browser process it launched. Nothing about that survives being loaded
into a page: there is no process to launch, no socket to open, and no
second browser to drive.

But the teaching requirement is unforgiving. The learner must write
**real, idiomatic, sync-API Playwright**, and it must **actually drive a
DOM** — no simulation, no pattern-matched fake, nothing that would make
`page.locator("#search_product").fill("dress")` succeed against a page
where that box does not exist. A learner who solves a challenge here has
to be able to paste the same characters into `tour-tests/` and watch them
pass against the real site.

Three pieces make that true:

| Piece | What it is | Where |
|---|---|---|
| **AutomationVille** | A static look-alike of automationexercise.com. Same ids, class names and headings. | `src/mockapp/` |
| **Pyodide** | Real CPython, compiled to WebAssembly. The learner's code is *executed*, not inspected. | `vendor/pyodide/` |
| **`playwright_lite`** | A Playwright-shaped shim that drives AutomationVille's DOM: auto-waiting, strict mode, Playwright's own error text. | `src/pylib/playwright_lite/` |

The shim is the interesting one, and the reason it can exist at all is
the bridge.

---

## 2. The bridge decision

### The constraint

`page.click()` is **synchronous**. It has to be — that is the API the
kit teaches, and `await page.click()` in a lesson would be teaching the
wrong library. So Python must block on a DOM operation and get an answer
back before the next line runs.

Two ways to do that in a browser:

**Option A — Pyodide in a Web Worker, DOM on the main thread.**
The worker posts a request, then blocks in `Atomics.wait()` on a
`SharedArrayBuffer` until the main thread writes the answer back. Python
blocks for real; the DOM is touched only by the thread that owns it.

**Option B — Pyodide on the main thread, DOM in a same-origin iframe.**
`iframe.contentDocument` is readable synchronously from the same thread.
There is nothing to wait *for*: the bridge call returns before it
returns. The cost is that the whole tab is frozen while Python runs, so
the app under test can have no real timers.

### The spike

The success criterion was one line running end to end against the real
mock DOM, before any content existed:

```python
page.locator("#search_product").fill("dress")
```

**Option B cleared it first, and cheaply** — no headers, no shared
memory, no worker protocol. It is what ships, and every test in
`tests/` exercises it.

Option A was costed rather than completed, because its blocking
requirement is a platform fact that does not need a prototype to
confirm: `SharedArrayBuffer` is unavailable without **cross-origin
isolation**, which needs `Cross-Origin-Opener-Policy` and
`Cross-Origin-Embedder-Policy` response headers. **GitHub Pages cannot
send them.** The workaround is a `coi-service-worker` that installs
itself and reloads the page on first visit — a service worker whose
failure mode is *the coding challenges silently stop working*, on a site
whose entire premise is that the coding challenges work. That is the
wrong risk to take for a benefit (a responsive tab during a 300 ms run)
this small.

### The decision: **Option B, main-thread Pyodide.**

The trade-offs, stated plainly:

| | Cost | Why it is acceptable here |
|---|---|---|
| **The tab freezes while a test runs** | The UI cannot repaint mid-run. | A challenge run is a few hundred milliseconds of Python against a DOM of ~200 nodes. Nobody is watching an animation during it. The *boot* — the 11 MB download — is `async` and does repaint, which is the part that actually takes time. |
| **A learner can hang the tab** | `while True: pass` freezes it until it is closed. | Accepted, and mitigated: `time.sleep` is replaced at boot (`quest/harness.py:install_guards`) with a raise that explains itself, and the rubric rejects sleeps *before* execution. An infinite loop is a genuine hole; the honest answer is that closing the tab loses nothing, because progress is saved before every run. |
| **No real timers in the app under test** | `setTimeout` cannot fire while Python holds the thread. | This turned into the best accident in the design. See below. |

### The virtual clock — a constraint that became a feature

Since real timers cannot fire, AutomationVille has none. It has a
**virtual clock** (`src/mockapp/app.js`): `clock.after(600, fn)` queues
an effect, and *nothing runs until someone calls `clock.advance()`*.

The only thing that calls `advance()` is the shim's auto-wait retry loop
(`playwright_lite/sync_api.py`). So:

- The search results appear **exactly** 600 virtual milliseconds after
  the click — every run, on every machine, forever.
- A learner who writes no wait sees the assertion fail against an empty
  page, deterministically, instead of "usually passing on a fast laptop".
- Auto-waiting is taught **faithfully** (the loop really does poll and
  really does re-check) and **reproducibly** (a flake here would be a
  bug, not weather).
- The site can report *"Page time used: 600 ms"* after a run, which is a
  concrete answer to "how long did `expect()` actually wait?"

A real clock could not do any of that. Retry cadence is fine-grained
(100 ms) for the first second and coarser (500 ms) after, so a 600 ms
round trip resolves at 600 ms while a genuinely doomed assertion still
reports quickly.

### The bridge interface

`src/js/bridge.js`. Deliberately made of **strings and numbers only** —
no JS objects cross into Python, and structured values travel as JSON.
Pyodide can proxy objects, but proxy lifetimes are the single most
common source of baffling Pyodide bugs, and an interface of strings is
one you can log, diff, and replay.

```
Python (Pyodide)                     JavaScript (main thread)
────────────────────                 ────────────────────────────
Locator.click()
  └─ chain -> JSON  ──────────────▶  bridge.perform(chainJson, "click", args, index)
                                       ├─ SelectorEngine.resolve(doc, chain)
                                       ├─ checkActionable(el, need)
                                       └─ el.click()
     retry loop     ◀──────────────  '{"ok":false,"code":"not_visible"}'
       └─ bridge.tick(100)  ───────▶  clock.advance(100)   (app effects fire)
       └─ ...until actionable, or TimeoutError with a Playwright-shaped call log
```

Locators are **data**, not closures: a chain of `{"k": "role", "role":
"link", "name": "Cart"}` steps. That one choice pays for itself three
times — the JS side resolves it, the Python side prints it back as
`get_by_role("link", name="Cart")` in error messages, and the grader
reads `kinds` off it to ask "was this a role locator?" without ever
looking at the learner's source.

### Sandboxing

The shop is an `<iframe sandbox="allow-scripts allow-same-origin
allow-forms">`. `allow-same-origin` is **required** — without it
`contentDocument` is null and the whole bridge collapses. It is not a
security boundary here and is not pretending to be one; it blocks
top-level navigation, popups and modal dialogs so learner code cannot
escape the panel it is meant to drive. The real boundary is that there
is no server, no credentials, and nothing to exfiltrate.

---

## 3. The grading model

**Never string-match the solution.** A learner who finds a better
locator than ours must pass. A learner who pastes our solution with a
sleep bolted on must not.

Four independent sources of truth, none of which is the learner's source
text:

1. **The action log** — every call that reached the page, recorded by
   `playwright_lite/_runtime.py`: method, target, locator kinds, args,
   whether it succeeded, and the virtual time it happened.
2. **The app snapshot** — AutomationVille's own state object after the
   run (`route`, `query`, `cart`, `searchResults`, …).
3. **The live DOM** — re-queried through the bridge for `dom` checks.
4. **The AST rubric** — `quest/rubric.py`, Python's own `ast` module,
   which is about *how it was written*.

### Order of operations

`quest/harness.py` runs one attempt in the order a good reviewer works:

```
1. Does it parse?            -> SyntaxError, with the line number
2. Would a reviewer approve? -> the AST rubric
3. Does it actually work?    -> execute against AutomationVille
4. Did it do the right thing? -> the challenge's checks (src/js/grade.js)
```

**Step 2 comes before step 3 on purpose.** Code containing
`time.sleep()` is never executed — partly because a sleep would freeze
the tab for real seconds, but mostly because *a senior reviewer stops at
the sleep too*. The feedback is the lesson; running it anyway would
undercut it.

### Why an AST and not a regular expression

Because grading must be about what the code **means**:

- `# never use time.sleep` is a comment, not a sleep.
- `assert page.get_by_text("Cart").is_visible()` is a real problem and
  contains the word "expect" nowhere.
- `page.locator("//div[@class='x']")` is an XPath even though it is a
  string argument like any other.

Parsing gets all three right; a regex gets all three wrong.

### The rules

| Rule | Severity | What it catches |
|---|---|---|
| `no-sleep` | error, **always on** | `time.sleep()`, `wait_for_timeout()` |
| `expect-over-assert` | error | `assert locator.is_visible()` and its eight siblings |
| `has-assertion` | error | A script that drives the page but can never fail |
| `test-function` | error | Nothing named `test_*` for pytest to collect |
| `no-locators-here` | error | A locator that escaped into a test file in a POM challenge |
| `no-xpath` | advice | XPath where a role locator would read better |
| `prefer-role-locator` | advice | `#id` / `.class` where the element has a visible name |

`no-sleep` is in `ALWAYS`: every challenge gets it whether it asks or
not. Everything else is opt-in per challenge, and a challenge can soften
a rule to advisory with `{"rule": "no-xpath", "severity": "advice"}`.

**`error` blocks. `advice` passes but costs the clean-run bonus.** Both
are written in the voice of a senior colleague leaving a kind, specific
PR comment — a red X teaches nothing, and "no `time.sleep`" without the
reason teaches only obedience.

### Behavioural checks

Declared per challenge as data (`src/js/grade.js` evaluates them):

| `kind` | Asks | Reads |
|---|---|---|
| `state` | Did the shop end up here? | snapshot |
| `dom` | Is this on screen now? | live DOM |
| `action` | Did your test *do* this? | action log |
| `matcher` | Did this `expect()` actually run? | action log |
| `locatorKind` | Did you use a role locator? | action log |
| `printed` | Did you print what was asked? | captured stdout |
| `virtualMs` | Did you wait out the page? | virtual clock |

`matcher` is worth dwelling on: it does not check that the learner
*typed* `to_be_visible`, it checks that a `to_be_visible` assertion
**executed and passed**. A line below a failure never counts.

`virtualMs` is only possible because of the virtual clock, and it is how
"your test finished before the results arrived" becomes a check rather
than a hunch.

---

## 4. The content pipeline

`build_site.py`, in the spirit of `docs/build_site.py`: plain Python, no
dependencies, no npm, readable top to bottom.

```
content/game.json          XP curve, levels, badges
content/about.md           the About page
content/zones/<nn>-<id>/
    zone.json              metadata, map position, prerequisites, objectives
    lesson.md              the prose
    challenges/*.json      one file per challenge, sorted by filename
src/                       app.css, js/, mockapp/, sw.js
src/pylib/                 the shim, the rubric, the harness
vendor/pyodide/            the Python runtime (fetch_vendor.py)
                │
                ▼
dist/           index.html, content.js, pylib.js, app.css, js/, mockapp/,
                sw.js, vendor/
```

Three decisions worth keeping:

**Content is data, never hand-written HTML.** Markdown prose is rendered
at *build* time by a ~90-line subset parser (headings, lists, fenced
code, `:::tip` callouts). The browser therefore ships no Markdown
parser, and a lesson author never writes a tag.

**Everything ships as two `<script>` files.** `content.js` sets
`window.QUEST_CONTENT`, `pylib.js` sets `window.QUEST_PYLIB` (the Python
sources as a `{path: source}` map, written into Pyodide's filesystem at
boot). Two requests instead of forty, no fetch waterfall, no loading
flash — and the shim is available offline before the service worker has
ever seen those paths.

**The build validates.** Missing required keys in a `zone.json` or a
challenge, or a `requires` naming a zone that does not exist, is a
`SystemExit` with the file path — not a blank screen at runtime.

The build id is a hash of the content payload, used to bust the cache on
`app.css`, `content.js` and `sw.js`. Unchanged files are skipped on
copy, because the vendored runtime alone is 11 MB and a no-op build
should not take a second.

### Load budget

| | Size | When |
|---|---|---|
| HTML + CSS + JS + content | **~180 KB** | first paint |
| Pyodide (`.wasm` + stdlib) | **~11 MB** | **only** when a coding challenge is first run |

The quest map, every lesson, every quiz and the whole progress system
work without Pyodide ever loading. The runtime downloads behind a
progress bar showing **real bytes** — the two big files are streamed
with `fetch` so the numbers are true, then `loadPyodide` reads them from
the HTTP cache. A fake spinner on an 11 MB download is a lie told to
someone on a slow connection.

A service worker makes the site work offline, with a split that matters:

- **The page itself is network-first**, cache as fallback. `index.html`
  is the document that pins every asset's `?v=<build id>`, so caching it
  first means a rebuilt site keeps loading the old page, which keeps
  requesting the old assets — and the learner never sees new content no
  matter how often they reload. It is a few hundred bytes; fetching it
  fresh costs nothing.
- **Everything else is cache-first.** Every one of those URLs is
  versioned, so a new build asks for new URLs and can never be handed a
  stale file.
- **The shell is precached at install**, from a list `build_site.py`
  generates. On a first visit the worker is not controlling the page
  yet, so nothing that load fetched passes through the fetch handler —
  without precaching, "works offline after the first visit" is simply
  untrue.
- **Pyodide is deliberately not in the shell.** It is 11 MB and the
  whole loading story is that it arrives only when a coding challenge
  needs it. It is cached lazily once fetched, so challenges work offline
  after their first run; lessons, quizzes and the map work offline
  immediately.

`tests/test_site_offline.py` holds all four in place, read from the
server side — from inside the page a cache hit and a network fetch look
identical.

Pyodide is **vendored** at a pinned version
(`fetch_vendor.py`, currently 0.28.3), not pulled from a CDN at runtime:
a third-party CDN is an availability dependency, a privacy leak, and a
supply-chain risk that a teaching site has no reason to take. An
unpinned "latest" would also silently change the Python running a
learner's code between two builds of the same site.

The editor is not vendored because there is nothing to vendor: it is a
real `<textarea>` with a syntax-highlighted `<pre>` painted behind it
(~170 lines, `src/js/editor.js`). CodeMirror and Monaco are excellent
and cost 300 KB–2 MB to solve a problem a `<textarea>` already solves —
screen readers, IME, undo, select-all, mobile keyboards — and
re-implementing that is how editors become inaccessible.

---

## 5. The game layer

Deliberately smaller than the teaching layer, and built on one rule:
**reward effort, never punish slowness.** No lives, no hearts, no timer
you can lose to, no way to go backwards. Frustration is not pedagogy.

- **XP** — per challenge, +50% first try, +25% for a clean review. Hints
  cost XP but there is a floor at 25% of base: asking for every hint and
  then solving it still pays.
- **Levels** — Intern → Automation Archmage, from `game.json`.
- **Badges** — declarative rules in `game.json` evaluated by
  `game.js:BADGE_RULES`. Each marks a *habit* ("Never Slept", "Selector
  Sniper"), not a number.
- **Unlocking** — a zone opens when every zone in its `requires` is
  fully cleared. A zone with no challenges yet can never be complete, so
  stubs read *"Coming soon"* and the zones behind them stay shut until
  the content exists. That is honest rather than tidy.

### Progress storage

One object in `localStorage` under `quest-for-automation.v1`, plus JSON
export/import so a learner can move machines or a bootcamp can collect
completions. **No accounts, ever** — that is a constraint, not a
shortcut. It means the site is a folder of static files, a learner needs
nobody's permission to start, and there is no database of names to lose.
The cost is that progress is per-browser, which is exactly what the
export button is for. Loads are merged over a default object, so a save
written by an older build still opens instead of throwing, and every
storage call is wrapped: private mode never breaks a lesson.

Everything else the site remembers is kept under its own key, never
inside that object:

| Key | Holds |
|---|---|
| `quest-for-automation.v1` | The progress object above — the only thing export/import moves |
| `quest-draft.<zone>/<challenge>` | Unsaved editor code, so closing the tab mid-challenge loses nothing |
| `quest-for-automation.theme` | Light or dark |
| `quest-for-automation.terrain` | Which map ground is showing |
| `quest-for-automation.accent` | Which accent scheme is applied |

The split is deliberate. Progress is the file a learner hands in, so a
display preference has no business travelling in it — and importing
somebody else's progress should not change your scenery or your theme.

### Accents

Five schemes (`src/js/main.js`), and they are curated PAIRS rather than a
colour wheel. The site uses two accents with jobs - the road you are on,
and the detour off it - so a scheme has to supply both, and both have to
hold up on warm cream *and* on green-black.

Most pairs a free colour picker would let you build fail that in one
theme or the other, which is the whole argument for a short list. Each
scheme sets its own `--accent-ink`, because whether white or near-black
belongs on the primary button flips between them.

`tests/test_site_banner.py` computes the real contrast ratios for every
scheme in both themes and fails under 4.5:1 for button text. It caught
the default: the design's `#1c8a60` gives white only 4.33:1, so the light
mint is a hair darker at `#1a845c`.

### The map's ground

Six backgrounds behind the same trail (`src/js/views/terrain.js`):
`blueprint` (the default), `survey`, `contours`, `terminal`, `night`,
`flat`. Only the default argues for anything — graph paper with the
wireframes of a product grid, a form and a cart, because the quest is
through *pages*, not mountains. The rest are scenery, and letting a
learner pick is the cheapest fun in the product.

All six are built once and switched with a `data-terrain` attribute on
`.map-board`. Changing ground is a class flip, never a re-render: a
re-render would restart the road's `qfa-dash` animation and re-read
progress for nothing. Every layer is `aria-hidden` — a screen reader
announcing hatching between the zone names would make the map worse.

Nothing in those grounds uses `<svg:text>`. The board shares its 0–100
coordinate space with the zones and is stretched to whatever aspect the
flex layout gives it, so a glyph in that space becomes a wedge; the
flavour lines are HTML captions positioned over the board instead.

---

## 6. Testing

Three layers, each fast where it can be:

| Suite | Runs | Covers |
|---|---|---|
| `tests/test_shim_unit.py` | plain pytest, milliseconds | The shim against a fake bridge: the retry loop, strict mode, timeout wording. No browser, no Pyodide. |
| `tests/test_site_*.py` | Playwright + pytest | The site itself, through a real Chromium. |
| The build | `build_site.py` | Content shape, required keys, prerequisite graph. |

The shim is split precisely so the first row is possible: it never
touches the DOM, it only asks a bridge to. Swap in a fake bridge and the
interesting half is testable in milliseconds. Which elements a selector
*actually* matches is JavaScript, and that half is covered by the
browser tests.

**The site that teaches Playwright is tested with Playwright**, using
this repo's own layering — tests assert, page objects hold every
locator. See `tests/README` notes in `tests/pages/`.

---

## 7. What was deliberately not built

Saying this out loud is the point of the document.

**In the bridge**

- **Web Worker + `SharedArrayBuffer`.** Spiked, worked, rejected on the
  COOP/COEP requirement. If the site ever needs true concurrency — a
  cancel button that works mid-run, an infinite loop that cannot hang the
  tab — this is the upgrade, and `bridge.js`'s string-only interface is
  already shaped to survive being made async.
- **A cancel button.** Follows from the above. There is nothing to
  cancel from while the thread is held.

**In the shim**

Nothing pretends to be there and quietly does nothing. Anything absent
raises `NotImplementedError` with a clear message:

- Frames, popups, multiple pages, `BrowserContext`.
- The network: no `route()`, no `expect_response()`, no `request`
  fixture. AutomationVille has no network to intercept.
- Screenshots, videos, traces, `page.pause()`. "Read the trace"
  challenges will therefore ship a *recorded* trace as content, not a
  live one.
- `async_api`. The kit teaches the sync API; two APIs would be two
  things to get wrong.

**In the runner**

- **pytest itself does not run.** The harness imitates its collection
  rule — functions named `test_*`, `page` injected only if the signature
  asks for it — because putting real pytest in Pyodide buys a plugin
  system nobody here uses and costs megabytes. The consequence is real
  and is written into the Fixture Foundry design: `conftest.py` cells
  are *executed and inspected*, not collected by pytest.
- **Parametrisation, markers, `-k` filtering.** The Runner's Gate zone
  teaches these as prose and quiz, not by executing them.

**In the game**

- Accounts, sync, leaderboards, comments, sharing. No backend means no
  moderation problem, no privacy policy, and no bill.
- Lives, hearts, countdowns, streak-loss penalties.

**In content**

- Zones 3 through ★ are **mapped, not built**: `zone.json` with real
  objectives and challenge titles, no `challenges/*.json` yet. The shape
  of the whole game is visible from the map; the engine needs no changes
  to fill them in.
- **Desktop Outpost is read-only by design.** pywinauto drives native
  Windows windows. It cannot run in a browser, will never run in a
  browser, and the zone says so on its face rather than faking it.

**Anywhere**

- No build tooling at the repo root, nothing added to
  `requirements.txt`, no npm. `python site/build_site.py` is the whole
  toolchain, and `docs/build_site.py` and `tour.py` are untouched.
