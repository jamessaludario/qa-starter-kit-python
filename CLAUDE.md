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

## Keep the halves in sync

If you improve the framework (pages/base_page.py, fixtures/, run_tests.py,
pytest.ini, requirements.txt), mirror the improvement into template/
(its generic, app-agnostic version) — and vice versa.


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
