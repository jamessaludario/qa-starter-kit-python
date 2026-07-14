# QA Automation Starter Kit — Python

> Learn UI test automation from zero, then generate tests for any web app.
> Playwright + Python (pytest) edition of the
> [qa-starter-kit](https://github.com/jamessaludario/qa-starter-kit) (TypeScript).

---

## 🌱 New to QA automation? Start here

Don't read anything yet — **do** the guided tour. It opens a real
browser so you can watch a test drive a website in slow motion, lets
you record your own script just by clicking around, and walks you into
writing your first test:

```bash
pip install -r requirements.txt
playwright install chromium
python tour.py
```

About 15 minutes, fully hands-on, quit and resume any time.

---

## What is this?

A hybrid **learning playground** and **ready-made test suite scaffold**:

1. **Learn QA automation** — 26 real, heavily-commented tests against the
   free practice site [automationexercise.com](https://automationexercise.com)
   (all 26 of its official test cases), an interactive tour, and a
   professionally layered framework to read and imitate.
2. **Scaffold tests for YOUR app** — one command copies a clean project
   skeleton, you add your app's URL, then write tests by hand or let an
   AI agent generate them using the included prompts.

**The kit provides:**
- 🧭 **Interactive tour** (`python tour.py`) — watch, record, then write
- 📚 **26 commented test cases** — a full suite to learn from
- 🏗️ **Scaffolder + template** — a fresh test project for any web app in seconds
- 🤖 **AI prompts + agent rules** — standardized prompts (scan → baseline → e2e → fix) and a `CLAUDE.md` convention file any agent can follow
- 📊 **Reports built in** — one-file HTML report, Allure dashboards with
  trends and failure screenshots, automatic retries for flaky moments
- 🚀 **CI included** — GitHub Actions runs the suite and publishes the live
  Allure report to GitHub Pages

---

## Supported AI agents

| Agent            | How to use                                          |
|------------------|-----------------------------------------------------|
| Claude Code      | Open your scaffolded folder in a terminal — rules in `CLAUDE.md` are picked up automatically |
| Cursor           | Copy `CLAUDE.md` to `.cursor/rules/qa-automation.mdc` |
| VS Code Copilot  | Copy `CLAUDE.md` to `.github/copilot-instructions.md` |
| Windsurf         | Copy `CLAUDE.md` to `.windsurf/rules.md`             |
| Any other agent  | Paste prompts from `prompts/` and reference `CLAUDE.md` |

---

## Quick start

### 🏁 Learn (recommended first step)

```bash
git clone https://github.com/jamessaludario/qa-starter-kit-python.git
cd qa-starter-kit-python
pip install -r requirements.txt
playwright install chromium

python tour.py           # the guided tour
pytest --headed --slowmo 500   # or just watch all 26 tests run
```

(Python 3.10+ required. Only the Allure analytics report additionally
needs Node.js — everything else works without it.)

### 🚀 Scaffold tests for YOUR web app

```bash
python scaffold.py
```

Two questions (project name, app URL) and you get a fresh, independent
project next to the kit:

```
../my-app-tests/     ← full structure, .env filled in, smoke test ready
```

Then:

```bash
cd ../my-app-tests
pytest tests/test_smoke.py     # proves the toolchain end to end
```

Grow the suite either way:
- **With an AI agent:** open the folder in your agent and feed it
  `prompts/00-quick-start.md`. The prompts walk it through scanning your
  app, generating baseline tests per page, building e2e journeys, and
  fixing failures — all following the conventions in `CLAUDE.md`.
- **By hand:** copy `pages/example_page.py.template`, build your first
  page object, write tests against it.

---

## Commands

> In the starter kit (learning):

```bash
python tour.py                  # interactive guided tour
pytest                          # run all 26 tests (headless)
pytest --headed --slowmo 500    # watch the browser work (great for learning!)
pytest -k "order"               # run a group of tests
python run_tests.py             # run everything + open the Allure report
python scaffold.py              # create a test project for your own app
```

> In your scaffolded project: the same commands, minus the tour.

**Automatic retries:** a failed test is retried up to 2 times before
counting as a real failure (`--reruns` in [pytest.ini](pytest.ini)) —
practice sites and real apps both have slow moments. Retries stay
visible in the reports, so flakiness is never silently hidden.

---

## Folder structure

The kit and every scaffolded project share the same layered layout:

```
your-app-tests/
├── tests/           ← WHAT to verify (assertions live here)
├── helpers/         ← reusable user journeys (login, create-record, ...)
├── pages/           ← page objects: ALL locators live here, one class per page
├── fixtures/        ← pytest plumbing: browser setup, screenshots, report labels
├── utils/           ← pure-Python tools (unique test data)
├── constants.py     ← app URL (from .env) + shared test data
├── conftest.py      ← thin loader that plugs the fixtures in
├── prompts/         ← copy-paste prompts for your AI agent
├── CLAUDE.md        ← conventions your AI agent follows
├── run_tests.py     ← run + build the Allure report in one command
└── .env             ← your app's URL (git-ignored)
```

The layering to remember: **tests** (what to verify) → **helpers**
(the journey) → **pages** (where things are). When the app changes,
you fix one locator in one page class — not every test.

## How the AI workflow works

1. **Scan** — your agent visits your app's pages and writes a map of
   elements and locators (`prompts/01-scan-pages.md`)
2. **Generate** — it turns the maps into page objects + baseline tests
   (`02-generate-baseline.md`), then full journeys (`03-generate-e2e.md`)
3. **Run** — pytest executes everything, reports with screenshots
4. **Fix** — paste failures into `04-fix-errors.md`; locators get fixed
   in the page objects, never papered over with sleeps
5. **Repeat** — re-scan when your app changes

---

## The learn track: 26 real test cases

Every file maps 1-to-1 to an official test case of the practice site and
is commented for beginners. Read them in order, or jump by topic:

| # | File | What it tests |
|---|------|---------------|
| 1 | [test_tc01_register_user.py](tests/test_tc01_register_user.py) | Register a new user (full flow) |
| 2 | [test_tc02_login_correct.py](tests/test_tc02_login_correct.py) | Login with correct credentials |
| 3 | [test_tc03_login_incorrect.py](tests/test_tc03_login_incorrect.py) | Login with wrong credentials shows error |
| 4 | [test_tc04_logout.py](tests/test_tc04_logout.py) | Logout returns to login page |
| 5 | [test_tc05_register_existing_email.py](tests/test_tc05_register_existing_email.py) | Duplicate email is rejected |
| 6 | [test_tc06_contact_us_form.py](tests/test_tc06_contact_us_form.py) | Contact form + file upload + browser dialog |
| 7 | [test_tc07_test_cases_page.py](tests/test_tc07_test_cases_page.py) | Test Cases page opens |
| 8 | [test_tc08_all_products_and_details.py](tests/test_tc08_all_products_and_details.py) | Product list + product detail page |
| 9 | [test_tc09_search_product.py](tests/test_tc09_search_product.py) | Search products |
| 10 | [test_tc10_subscription_home.py](tests/test_tc10_subscription_home.py) | Footer subscription (home page) |
| 11 | [test_tc11_subscription_cart.py](tests/test_tc11_subscription_cart.py) | Footer subscription (cart page) |
| 12 | [test_tc12_add_products_in_cart.py](tests/test_tc12_add_products_in_cart.py) | Add two products, verify prices/totals |
| 13 | [test_tc13_product_quantity_in_cart.py](tests/test_tc13_product_quantity_in_cart.py) | Quantity 4 shows up in cart |
| 14 | [test_tc14_order_register_while_checkout.py](tests/test_tc14_order_register_while_checkout.py) | Full order — register during checkout |
| 15 | [test_tc15_order_register_before_checkout.py](tests/test_tc15_order_register_before_checkout.py) | Full order — register first |
| 16 | [test_tc16_order_login_before_checkout.py](tests/test_tc16_order_login_before_checkout.py) | Full order — login first |
| 17 | [test_tc17_remove_product_from_cart.py](tests/test_tc17_remove_product_from_cart.py) | Remove product from cart |
| 18 | [test_tc18_view_category_products.py](tests/test_tc18_view_category_products.py) | Category sidebar (Women/Men) |
| 19 | [test_tc19_view_brand_products.py](tests/test_tc19_view_brand_products.py) | Brand pages (Polo/H&M) |
| 20 | [test_tc20_search_and_verify_cart_after_login.py](tests/test_tc20_search_and_verify_cart_after_login.py) | Cart survives logging in |
| 21 | [test_tc21_add_review_on_product.py](tests/test_tc21_add_review_on_product.py) | Submit a product review |
| 22 | [test_tc22_recommended_items.py](tests/test_tc22_recommended_items.py) | Add to cart from carousel |
| 23 | [test_tc23_address_details_in_checkout.py](tests/test_tc23_address_details_in_checkout.py) | Checkout shows registered address |
| 24 | [test_tc24_download_invoice.py](tests/test_tc24_download_invoice.py) | Download invoice after purchase |
| 25 | [test_tc25_scroll_up_with_arrow.py](tests/test_tc25_scroll_up_with_arrow.py) | Scroll-up arrow button |
| 26 | [test_tc26_scroll_up_without_arrow.py](tests/test_tc26_scroll_up_without_arrow.py) | Scroll up with JavaScript |

Where to start reading:
1. [test_tc01_register_user.py](tests/test_tc01_register_user.py) — a
   full flow written out step by step
2. [helpers/flows.py](helpers/flows.py) then
   [pages/base_page.py](pages/base_page.py) — how a helper like
   `create_account()` is built from page-object methods

Good to know:
- Tests that need an account **create their own throwaway account**
  (unique email each run) and **delete it at the end** — every test is
  self-contained and can run alone, in any order.
- The order tests (14, 15, 16, 24) pay with an obviously **fake card
  number** — it's a practice site, no real payment happens.

---

## Test reports

Every run produces two kinds of results in the (git-ignored) `reports/`
folder:

**1. Quick HTML report** — `reports/report.html`, a single
self-contained file: pass/fail per test, durations, full error details.
Double-click to open.

> pytest-html is pinned to 3.x on purpose: version 4+ fills the results
> table with JavaScript, which shows up EMPTY in viewers that block
> scripts. 3.x writes plain HTML that displays anywhere.

**2. Graphs & analytics (Allure)** — status charts, duration graphs,
failure screenshots attached to each failed test, defect density per
feature area (Behaviors tab), and trend graphs across runs:

```bash
# one-time: the Allure CLI (needs Node.js; runs on Java 8+)
npm install -g allure-commandline

# then this one command runs tests, keeps trend history, builds and
# opens the report:
python run_tests.py
```

(Allure reports are served over a local web server — `run_tests.py` and
`allure open` handle that; don't open its index.html from the file
system.)

## Reports in CI (GitHub Actions)

[.github/workflows/tests.yml](.github/workflows/tests.yml) runs the
suite on every push to `main` and delivers the reports two ways:

- **Live Allure report on GitHub Pages** — every run publishes to
  <https://jamessaludario.github.io/qa-starter-kit-python/>, history
  carried between runs so the trend graphs grow in CI too.
- **Downloadable artifact** — each run attaches `test-reports` (the
  self-contained `report.html` plus the Allure folder).

The workflow still turns red when tests fail — the report is published
*first*, then the real test result is reported, so a red run always has
its report attached. Scaffolded projects get a simpler artifact-only
workflow in `template/.github/workflows/tests.yml`.

---

## Key ideas to remember

- **`page`** — a browser tab Playwright controls. pytest-playwright gives
  every test a fresh one automatically.
- **`expect(...)`** — a check that *waits automatically* for the condition
  to become true. You never need `time.sleep()` in Playwright.
- **Locators** — find elements the way a *user* would:
  `page.get_by_role("link", name="Products")` beats brittle CSS.
- **A test = Arrange, Act, Assert** — prepare what you need, do the
  action, check the result.
- **Page objects** — all locators in one class per page, so app changes
  mean one fix, not twenty.

## Ideas to try next

1. Change the search word in test case 9 from `"dress"` to `"top"`.
2. In test case 13, try a different quantity.
3. Add a new test: what happens when you search for something that
   doesn't exist (e.g. `"xyz123"`)?
4. Try Firefox: `pytest --browser firefox` (first:
   `playwright install firefox`).
5. Scaffold a project for a site you use daily and let your AI agent
   build its baseline suite.
