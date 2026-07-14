# AI agent instructions — qa-starter-kit-python

This repo is a LEARNING KIT and TEMPLATE SOURCE, not an ordinary test
suite. It has two halves:

1. **The learn track** — 26 heavily-commented Playwright + pytest tests
   against https://automationexercise.com (tests/), an interactive tour
   (tour.py), and a layered framework (pages/, helpers/, fixtures/,
   constants.py, utils/).
2. **The scaffold** — template/ (a generic project skeleton), prompts/
   (AI prompts), and scaffold.py which copies both into a fresh
   project for the user's own app.

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

- Quick check: `python -m pytest tests/test_tc07_test_cases_page.py --reruns 0`
- Scaffold check: `python scaffold.py --name tmp --url https://example.com --dest <temp dir>`
  then run its smoke test and delete the folder.
- The tour must keep working: `echo 1 | python tour.py` should print
  chapter 1 without errors.
