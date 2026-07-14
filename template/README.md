# {{PROJECT_NAME}} — automated UI tests

Playwright + Python (pytest) test suite for **{{PROJECT_NAME}}**,
scaffolded from the
[qa-starter-kit-python](https://github.com/jamessaludario/qa-starter-kit-python).

## Setup (once)

```bash
pip install -r requirements.txt
playwright install chromium

# your app's address lives in .env (git-ignored)
# it was created by the scaffolder — check the values:
#   PROJECT_NAME=...
#   BASE_URL=...
```

Prove the toolchain works end to end:

```bash
pytest tests/test_smoke.py
```

## Growing the suite

Two ways — mix freely:

**With an AI agent** (Claude Code, Cursor, Copilot, Windsurf, ...):
open this folder in your agent and feed it the prompts in
[prompts/](prompts/), starting with `00-quick-start.md`. The agent's
rules live in [CLAUDE.md](CLAUDE.md) (copy it to your agent's rules
location if it isn't Claude).

**By hand:** copy
[pages/example_page.py.template](pages/example_page.py.template) to
create your first page object, then write tests that use it. The
architecture:

```
tests/      WHAT to verify              (assertions)
helpers/    reusable user journeys      (login, create-record, ...)
pages/      page objects                (ALL locators live here)
constants.py  app URL + shared data    fixtures/  pytest plumbing
```

## Running

```bash
pytest                        # everything, headless
pytest --headed --slowmo 500  # watch the browser work
pytest -k "login"             # tests matching a word
python run_tests.py           # everything + Allure report in browser
```

Every run writes `reports/report.html` (double-click to open). Failures
automatically attach a full-page screenshot to the Allure report.
