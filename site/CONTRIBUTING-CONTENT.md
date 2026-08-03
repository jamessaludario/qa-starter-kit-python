# Adding a challenge or a zone

**One challenge is one JSON file. You never touch engine code.**

If you find yourself editing anything in `src/js/` or `src/pylib/` to add
content, stop — either the thing you want already exists under a
different name, or it is a genuine engine gap worth discussing before it
becomes a special case.

```bash
python site/build_site.py
```

Builds, serves on <http://127.0.0.1:8000/>, and opens a browser. The
build validates your file and tells you exactly which key is missing.

---

## The layout

```
content/
  game.json                        XP curve, levels, badges
  about.md                         the About page
  zones/
    00-base-camp/
      zone.json                    metadata, map position, prerequisites
      lesson.md                    the prose
      challenges/
        01-first-test.json         one challenge
        02-what-pytest-collects.json
```

Folders and files sort by name, which is why they are numbered. The
number is ordering only — the `id` inside is what the site uses.

---

## Adding a challenge

Drop a numbered `.json` file into a zone's `challenges/` folder. That is
the whole procedure.

### The shape

```jsonc
{
  "id": "search-for-a-dress",       // required, unique within the zone, used in the URL
  "title": "Search for a dress",    // required
  "kind": "write-the-test",         // required, see the table below
  "xp": 30,                         // required
  "boss": false,                    // optional, adds the Boss tag

  "brief": "Markdown. The task.",   // rendered at build time
  "scenario": { "route": "/products" },

  "starter": "from playwright...",  // pre-filled in the editor
  "solution": "...",                // never shown; for reviewers and for tests

  "rubric": ["test-function", "has-assertion"],
  "checks": [ ... ],
  "hints": [ ... ],
  "reveal": "Markdown, shown after they pass."
}
```

Required: `id`, `title`, `kind`, `xp`. Everything else is optional and
the engine has a sane default.

`brief`, `reveal` and quiz prompts are **Markdown**, rendered at build
time. Supported: `##`–`####` headings, paragraphs, `-`/`1.` lists,
`**bold**`, `*italic*`, `` `code` ``, fenced code blocks, links, and
`:::tip` / `:::warn` / `:::note` callouts. That is the whole subset — if
you need more, the lesson probably needs less.

:::note
Write JSON strings with real `\n` escapes for newlines in `starter` and
`solution`. It is ugly and it is the price of not inventing a file
format.
:::

### The kinds

| `kind` | What the learner gets | Graded on |
|---|---|---|
| `write-the-test` | An empty-ish editor and a task | rubric + checks |
| `fill-the-blank` | A `starter` with the hard line missing | rubric + checks |
| `fix-the-broken-test` | A `starter` that runs and is wrong | rubric + checks |
| `spot-the-flake` | A `starter` that passes by luck | rubric + checks |
| `refactor-to-pom` | Multiple editors (`cells`) | rubric per cell + checks |
| `locator-match` | A one-line locator box + live DOM highlighting | checks |
| `quiz` | Multiple-choice questions | all answers correct |
| `predict-the-error` | Quiz whose options are error messages | all answers correct |
| `read-the-trace` | Quiz over a supplied trace/log | all answers correct |

The first six all use the same code path; the difference is entirely in
the `starter` you write and the `checks` you ask for. Vary them — ten of
the same exercise is ten times the same lesson.

---

## `scenario` — the shop's starting state

Reset before **every** run, so a run never inherits the one before it —
the same discipline the kit asks of its own tests.

| Key | Effect |
|---|---|
| `route` | Which page to open, e.g. `"/products"`, `"/login"`, `"/view_cart"` |
| `consent` | `true` puts the cookie-consent overlay in the way |
| `cart` | `[{"id": 3, "qty": 2}]` — pre-fill the cart |
| `account` | `{"name","email","password"}` — pre-register, so a login lesson need not sign up first |
| `loggedInAs` | `{"name","email"}` — start logged in |
| `viewing` | Product id for `/product_details/<id>` |
| `latency` | Multiplier on every delay. `2` makes the shop twice as slow. |

The catalogue is eight fixed products (ids 1–8; two are dresses). It is
in `src/mockapp/app.js` and is deliberately small enough to reason about.

---

## `checks` — grading on behaviour

Checks never look at the learner's source. They ask what their code
**did**, and where the shop **ended up**. Find a better locator than ours
and you pass; paste ours with a sleep bolted on and you do not.

| `kind` | Fields | Asks |
|---|---|---|
| `state` | `path`, comparator | Where did the shop end up? |
| `dom` | `selector`, comparator | How many of these are on screen now? |
| `action` | `method`, `targetContains`, `value`, `locatorKind`, `atLeast` | Did the test *do* this? |
| `matcher` | `name`, `atLeast` | Did this `expect()` run **and pass**? |
| `locatorKind` | `name`, `atLeast` | Did they use this *kind* of locator? |
| `printed` | `contains` | Did they print it? |
| `virtualMs` | comparator | Did they wait out the page? |

Comparators, usable on any check that takes one: `equals`, `notEquals`,
`atLeast`, `atMost`, `contains`, `isTrue`, `isFalse`. More than one on
the same check means all must hold.

Every check may carry:

- `label` — what the learner sees in the "What I checked" list. Write it
  as the *behaviour being proved*, not as the mechanism.
- `feedback` — shown only when it fails. **Write one.** The default is
  generic, and a failing check with a generic message is the red X this
  site exists to avoid.

### `state` paths

From the shop's snapshot: `route`, `url`, `query`, `searching`,
`searchResults`, `cartCount`, `cartUnits`, `cartItems`, `user`,
`userEmail`, `accounts`, `loginError`, `signupError`, `subscribed`,
`contactSent`, `orderPlaced`, `invoiceDownloaded`, `accountDeleted`,
`consentOpen`, `cartModal`, `virtualMs`. Dotted paths index into
arrays: `cartItems.0.qty`.

### `action` methods and `locatorKind` names

Methods are the shim's own: `goto`, `click`, `fill`, `check`, `uncheck`,
`select_option`, `press`, `hover`, `inner_text`, `all_inner_texts`,
`count`, `is_visible`, `get_attribute`, and `expect.<matcher>`.

Locator kinds: `role`, `text`, `label`, `placeholder`, `testid`,
`alttext`, `title`, `css`, `xpath`, `filter`, `first`, `last`, `nth`.

### Example

```jsonc
{
  "kind": "matcher",
  "name": "to_have_count",
  "label": "You assert exactly how many results there are",
  "feedback": "No to_have_count check ran. \"Some results\" is a weak promise — say how many, and the test notices when the search starts over-matching."
}
```

---

## `rubric` — grading on craft

Names from `src/pylib/quest/rubric.py`. Listed rules run **in addition**
to `no-sleep`, which is always on.

| Rule | Default | Catches |
|---|---|---|
| `no-sleep` | error, always | `time.sleep()`, `wait_for_timeout()` |
| `expect-over-assert` | error | `assert locator.is_visible()` |
| `has-assertion` | error | A script that can never fail |
| `test-function` | error | Nothing named `test_*` |
| `no-locators-here` | error | A locator in a file that should have none |
| `no-xpath` | advice | XPath where a role locator would read better |
| `prefer-role-locator` | advice | `#id`/`.class` where the element has a visible name |

Soften one for a challenge where it would be unfair:

```jsonc
"rubric": ["test-function", { "rule": "prefer-role-locator", "severity": "advice" }]
```

**`error` blocks and the code is never run. `advice` passes but costs the
clean-run bonus.** Choose deliberately: a rule that blocks before the
learner has been taught the alternative is a trap, not a lesson.

Adding a *new* rule is engine work — `rubric.py` plus a unit test in
`tests/test_shim_unit.py`. Keep the bar high: every rule is a thing a
learner can fail on, so it had better be something a senior engineer
would genuinely block a PR over.

---

## `hints` — tiered, and they cost XP

```jsonc
"hints": [
  { "cost": 3,  "label": "Nudge",    "text": "..." },
  { "cost": 5,  "label": "Strategy", "text": "..." },
  { "cost": 8,  "label": "Solution", "text": "..." }
]
```

Three tiers is the house style: **nudge** (which tool), **strategy**
(the shape of the answer), **solution** (the line). The cost exists so a
learner pauses before opening one, not to punish them — XP never falls
below 25% of the challenge's base, so asking for all three and then
solving it still pays.

---

## Challenge-specific fields

### `locator-match`

```jsonc
{
  "kind": "locator-match",
  "expectCount": 1,                                    // required
  "placeholder": "get_by_role(\"link\", name=\"Cart\")",
  "starter": "",
  "template": "..."                                    // optional, {{expr}} and {{count}}
}
```

The learner types only what follows `page.`. It is spliced into a real
test that asserts the match count, and whatever matched is outlined in
the shop panel.

### `refactor-to-pom` and anything with extra files

```jsonc
"cells": [
  {
    "name": "pages/product_page.py",
    "label": "The page object",
    "starter": "class ProductPage:\n    ...",
    "rubric": []
  }
],
"rubric": ["no-locators-here"]
```

Each cell becomes its own editor and its own real file on Pyodide's
filesystem, importable from the test. `__init__.py` files are created
automatically, because nobody should have to remember that in a browser
text box. Note the split above: `no-locators-here` on the **test**,
nothing on the page object — that is the layering being enforced.

### `quiz`, `predict-the-error`, `read-the-trace`

```jsonc
"questions": [
  {
    "prompt": "Markdown.",
    "code": "optional code sample, shown verbatim",
    "options": ["...", "...", "..."],
    "answer": 1,                                      // 0-based
    "why": "Explain it whether they got it right or wrong."
  }
]
```

Every question needs a `why`, and it is shown for correct answers too. A
learner who guessed right and does not know why has learned nothing.

---

## Adding a zone

Create `content/zones/<nn>-<slug>/zone.json`:

```jsonc
{
  "id": "form-marshes",             // required, unique, used in the URL
  "order": 3,                       // required, position on the map
  "badge": "3",                     // shown in the map node
  "title": "The Form Marshes",      // required
  "tagline": "One sentence.",       // required
  "teaches": "fill, check, select_option, negative cases",
  "source": ["guide §6", "learn/test_tc01"],
  "requires": ["assertion-ridge"],  // cleared before this opens
  "map": { "x": 58, "y": 55 },      // percent of the map board
  "objectives": ["By the end you can ..."],
  "plannedChallenges": ["Titles, while the zone is still a stub"]
}
```

Then add `lesson.md` beside it, and `challenges/` when you have some.

**A zone with no challenges is a valid, shipped stub** — the map shows
it, the zone page lists `plannedChallenges`, and zones behind it stay
locked (a zone with no challenges can never be "cleared"). That is
honest: the shape of the game is visible without pretending the content
exists.

`requires` naming a zone that does not exist is a build error, not a
blank screen.

### The lesson

`lesson.md`, same Markdown subset. Keep it **short**. The long version is
`docs/qa-automation-guide.html`, which stays the source of truth —
if your lesson and the guide disagree, the guide wins and one of them is
a bug.

Read a little, then do a lot. If the lesson is longer than the
challenges, the zone is a document with a quiz attached.

---

## Badges and levels

`content/game.json`. Levels are `{ "xp": 800, "title": "SDET" }`.

Badge rules are declarative, evaluated by `src/js/game.js`:

| `type` | Fields |
|---|---|
| `challengesPassed` | `value` |
| `firstTryPasses` | `value` |
| `passedWithoutHints` | `value` |
| `bossesCleared` | `value` |
| `zoneCleared` | `zone` |
| `zoneCleanOfSleep` | `zone` |
| `statAtLeast` | `stat`, `value` (stats: `runs`, `roleLocators`, `sleepAttempts`, `cleanRuns`) |

A badge should mark a **habit worth having**, not a number worth
chasing. "Never Slept" is a badge; "Ran 50 tests" is a scoreboard.

A new rule *type* is engine work. A new badge using an existing type is
data.

---

## House style for writing content

The teaching outranks the polish. Everything below is a rule the kit
already lives by (`CLAUDE.md`), applied to prose:

- **Every code sample is code you would approve in a real PR.** No
  `time.sleep()`. No locators in tests. No bare
  `assert element.is_visible()` where `expect()` belongs. No XPath where
  a role selector exists.
- **Never teach a technique the kit's own tests do not use.** If it is
  not in `learn/`, `pages/` or `helpers/`, it does not belong in a
  lesson.
- **Feedback is a PR comment from a senior colleague**: kind, specific,
  and it says *why*. "No `time.sleep`" without the reason teaches only
  obedience.
- **Say what the learner gains**, not what they got wrong.
- **ASCII in anything that reaches a console.** Learners' terminals are
  often cp1252.
- Files are **UTF-8**, explicitly.

---

## Before you open a PR

```bash
python site/build_site.py --build-only   # validates content, prints the counts
python -m pytest site/tests/             # the site's own suite
```

Then actually play your challenge:

1. Submit the wrong answer first. Is the feedback useful, or just red?
2. Submit an answer that is *right but different from yours*. Does it
   pass? (If not, your `checks` are string-matching by another name.)
3. Submit it with a `time.sleep(2)` bolted on. It must be rejected
   before it runs.
4. Open every hint and check the XP still lands above the floor.
