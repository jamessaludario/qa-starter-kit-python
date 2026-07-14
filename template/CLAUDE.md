# AI agent instructions for this test project

This is a Playwright + Python (pytest) UI test suite. Follow these
conventions for ALL code you generate or modify here. (Using Cursor,
Copilot, or Windsurf instead of Claude? Copy this file to your agent's
rules location — `.cursor/rules/`, `.github/copilot-instructions.md`,
`.windsurf/rules.md` — it is written to work for any agent.)

## Architecture (never bypass the layers)

```
tests/      WHAT to verify — assertions live here, locators do not
helpers/    user journeys shared by many tests (login, create-record...)
pages/      page objects — ALL locators live here, one class per page
constants.py  app URL (from .env) and shared test data
fixtures/   pytest fixtures/hooks (browser setup, reporting)
utils/      pure-Python tools (unique data generators)
```

- Tests call helpers and page objects; they must not contain raw
  selectors. If a test needs a new element, add it to the page object.
- New page = new file `pages/<name>_page.py`, class inheriting
  `BasePage`, with a `path` attribute. Export it from `pages/__init__.py`.
- Multi-page journeys used by 2+ tests belong in `helpers/flows.py`.

## Writing style

- Locators, in order of preference: `get_by_role(name=...)`,
  `get_by_label`, `get_by_text`, `data-testid`/`data-qa` attributes,
  CSS as a last resort. Never XPath, never positional (`nth`) unless
  the list itself is the subject.
- Every wait is an `expect(...)` assertion — NEVER `time.sleep()`.
- Every test must be self-contained: it creates the data it needs
  (use `utils/data.py` generators) and cleans up after itself.
- Comment generously: this project's readers may be learning. Explain
  WHY, especially around waits and reliability patterns.
- One behavior per test; name it `test_<behavior>` in a file
  `tests/test_<area>_<behavior>.py`.

## Workflow

- Run a single test: `python -m pytest tests/<file> --reruns 0`
- Run everything + report: `python run_tests.py --no-open`
- A failing test attaches a full-page screenshot to the Allure results
  automatically — check `reports/` before guessing at causes.
- When you add tests for a new area of the app, add the area to
  `FEATURE_AREAS` in `fixtures/reporting.py` so reports group it.

## Guardrails

- Never commit `.env` (it contains the app URL and any credentials).
- Never hard-code credentials or URLs in tests — use `constants.py`.
- Do not change `pytest.ini` retry settings to make flaky tests pass;
  fix the wait/locator instead.
