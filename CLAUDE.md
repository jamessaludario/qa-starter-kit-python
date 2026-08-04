# AI agent instructions — qa-starter-kit-python

This repo is a LEARNING KIT and TEMPLATE SOURCE, not an ordinary test
suite. It has two halves:

1. **The learn track** — 26 heavily-commented Playwright + pytest tests
   against https://automationexercise.com (sources in learn/; the tour
   copies them to the git-ignored tour-tests/, the learner's sandbox
   and the pytest testpath), an interactive tour (tour.py), and a
   layered framework (pages/, helpers/, fixtures/, constants.py,
   utils/).
2. **The scaffold** — template/ (a generic project skeleton), prompts/
   (AI prompts), and scaffold.py which copies both into a fresh
   project for the user's own app (components selectable via
   --include). The repo is also a GitHub template ("Use this
   template"), so users can copy it without cloning.

Plus a smaller third piece, **the desktop track** (desktop/): the same
layering applied to native Windows apps with pywinauto, since Playwright
cannot drive them. It is deliberately self-contained — its own conftest.py,
fixtures, and requirements-desktop.txt — because pywinauto is Windows-only
and the web track must stay installable everywhere. Section 12 of
docs/qa-automation-guide.html is its tutorial; keep the two in step.

And a fourth, **the quest site** (site/): "Quest for Automation", a
static browser game that teaches the same material by running the
learner's real Playwright Python in the page. Pyodide executes it; a
shim (site/src/pylib/playwright_lite/) drives a mock shop's DOM with
faithful auto-waiting, strict mode and Playwright's own error messages.
It is a re-presentation of assets that already exist — learn/, pages/,
helpers/ and docs/qa-automation-guide.html stay authoritative. Read
site/ARCHITECTURE.md before touching site/src/; it records the bridge
decision, the grading model, and what was deliberately not built.

## Conventions when editing here

- Comment style: this is teaching material. Every non-obvious line gets
  a WHY comment, written for a beginner. Match the existing voice.
- Architecture layers (both in the kit and the template):
  tests (assertions) -> helpers (journeys) -> pages (ALL locators).
  Never put locators in tests.
- Waits are always `expect(...)` assertions — never `time.sleep()`.
- Tests are self-contained: create own data (utils/), clean up after.
- Windows-friendliness matters: write files as UTF-8 explicitly, keep
  CLI output ASCII (learners' consoles are often cp1252).

## Keep the tracks in sync

If you improve the framework (pages/base_page.py, fixtures/, run_tests.py,
pytest.ini, requirements.txt), mirror the improvement into template/
(its generic, app-agnostic version) — and vice versa.

The quest site is a fourth thing to keep in step, in one direction:
learn/, pages/, helpers/ and the guide are the source of truth, and
site/content/ re-presents them. So:

- Change a convention (a new rubric rule, a different locator habit)?
  Update rubric.py in site/src/pylib/quest/ AND the lesson that teaches
  it, or the site starts marking learners against a rule nobody told
  them about.
- Change a learn/ test the site rebuilds as a challenge (TC01-03, 05-07,
  09, 12, 13, 17)? Re-check that challenge's `solution` still passes —
  site/tests/test_site_solutions.py runs every shipped solution and will
  tell you.
- Never teach a technique in site/content/ that the kit's own tests do
  not use, and never let a lesson contradict
  docs/qa-automation-guide.html. The guide wins.
- Adding a challenge or a zone should be a data change only. If it needs
  engine code, say so out loud — see site/CONTRIBUTING-CONTENT.md.


## "Use this template" must stay clean

GitHub copies a template repo WHOLE - there is no way to exclude a
folder - so `.github/template-cleanup.py` strips the learning material
out of a generated copy on its first push, and the workflow beside it
then deletes both.

It is deliberately a KEEP list (`prompts`, `.github`, `.git`,
`template`), not a delete list. Add a fifth track tomorrow and it is
removed by default. That direction is the point: the failure mode should
be "a new folder went missing from people's projects", which somebody
notices immediately, and never "the learning kit leaked into every
project", which nobody notices for months.

So: **do not add a new top-level folder to KEEP_AT_ROOT unless a real
project genuinely needs it.** What the cleanup leaves behind must stay
identical to what `python scaffold.py` produces - two definitions of "a
clean project" would drift apart within a month. Check it after any
change to `template/`, `scaffold.py` or the repo's top level - and check
it in a THROWAWAY copy, never here:

    git archive HEAD | tar -x -C /tmp/kitcheck
    cd /tmp/kitcheck && git init -q . \
      && git remote add origin https://example.com/copy.git
    python .github/template-cleanup.py --yes --ci

The script refuses to run when `origin` points at this repo, which is
what stops somebody pasting the command out of the README and deleting
their own learning checkout. Do not weaken that guard: everything it
removes is committed and restorable with `git restore .`, but
`site/vendor/` and `site/dist/` are git-ignored and have to be fetched
and built again.

## Testing changes

- Quick check: `python tour.py --create-tests` then
  `python -m pytest tour-tests/test_tc07_test_cases_page.py --reruns 0`
- Scaffold check: `python scaffold.py --name tmp --url https://example.com --dest <temp dir>`
  then run its smoke test and delete the folder. Also spot-check a
  partial layout, e.g. `--include none` and `--include pages`.
- The tour must keep working: `echo 1 | python tour.py` should print
  chapter 1 without errors.
- Desktop check (Windows, on an unlocked desktop): `python desktop/run_tests.py`.
  These drive real windows, so they cannot run headless or over a
  disconnected RDP session.
- Docs check: after editing docs/qa-automation-guide.html (the source of
  truth), rebuild with `python docs/build_site.py --no-open`. New sections
  must also be registered in build_site.py (SECTIONS + SIDEBAR_GROUPS) and
  in the guide's own table of contents.
- Quest site check: `python site/build_site.py --build-only` (it
  validates the content and fails loudly on a missing key), then
  `python -m pytest site/tests/`. The fast half needs no Python runtime;
  the `slow` half boots Pyodide in a real browser and needs
  `python site/fetch_vendor.py` to have run once. `-m "not slow"` while
  iterating. The site that teaches Playwright is tested with Playwright,
  page objects and all — keep it that way.
