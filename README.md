# QA Automation Starter Kit — Python

> Learn UI test automation from zero, then generate tests for any web app.
> Playwright + Python (pytest) edition of the
> [qa-starter-kit](https://github.com/jamessaludario/qa-starter-kit) (TypeScript).

[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?style=for-the-badge&logo=github)](https://github.com/jamessaludario/qa-starter-kit-python/generate)

Click **Use this template** to get your own independent copy of the kit
on GitHub — the original stays untouched, and your copy is 100% yours
to edit.

**Jump to:** [Pick your path](#pick-your-path) ·
[Guided tour](#-start-the-guided-tour-15-minutes-zero-experience-needed) ·
[Quick start](#quick-start) ·
[Commands](#commands-cheat-sheet) ·
[AI workflow](#-how-the-ai-workflow-works) ·
[Troubleshooting](#-troubleshooting)

---

## Pick your path

Everyone lands here for a different reason. Find your row:

| You are... | Do this |
|---|---|
| 🌱 Brand new to test automation | Run the **[guided tour](#-start-the-guided-tour-15-minutes-zero-experience-needed)** below — no reading required |
| 📖 The type who wants concepts explained first | Open the **[interactive docs guide](docs/qa-automation-guide.html)** — Playwright, locators, assertions, reports, all from zero |
| 🚀 Comfortable with the basics, testing my own app now | Jump straight to **[Test your own app](#-test-your-own-app)** |
| 🤖 Want an AI agent to write the tests for me | Jump to **[How the AI workflow works](#-how-the-ai-workflow-works)** |

---

## 🌱 Start the guided tour (15 minutes, zero experience needed)

Don't read anything yet — **do** the guided tour. It sets up your own
sandbox copy of the practice tests, opens a real browser so you can
watch a test drive a website in slow motion, lets you record your own
script just by clicking around, and walks you into writing your first
test.

```bash
pip install -r requirements.txt
playwright install chromium
python tour.py
```

By the end, you'll have:

- [ ] Watched a real browser run an automated test, in slow motion
- [ ] Learned what a locator is and how tests find things on a page
- [ ] Recorded your own click-path into working code
- [ ] Written and run your first test, from scratch
- [ ] Opened an HTML report of the results

Quit any time with `q` — `python tour.py` always drops you back at the
same menu. Something not working? See [Troubleshooting](#-troubleshooting).

---

## What's inside

A hybrid **learning playground** and **ready-made test suite scaffold**:

1. **Learn QA automation** — 26 real, heavily-commented tests against the
   free practice site [automationexercise.com](https://automationexercise.com)
   (all 26 of its official test cases), an interactive tour, and a
   professionally layered framework to read and imitate.
2. **Scaffold tests for YOUR app** — one command copies a clean project
   skeleton, you add your app's URL, then write tests by hand or let an
   AI agent generate them using the included prompts.

<details>
<summary><strong>See everything the kit provides</strong></summary>

- 🧭 **Interactive tour** (`python tour.py`) — watch, record, then write
- 📚 **26 commented test cases** — pristine sources in [learn/](learn/),
  your editable sandbox copy in `tour-tests/` (created by the tour,
  git-ignored — break things freely, fresh copies on demand)
- 🏗️ **Scaffolder + template** — a fresh test project for any web app in
  seconds, with the framework pieces you want
- 🤖 **AI prompts + agent rules** — standardized prompts (scan → baseline
  → e2e → fix) and a `CLAUDE.md` convention file any agent can follow
- 📊 **Reports built in** — one-file HTML report, Allure dashboards with
  trends and failure screenshots, automatic retries for flaky moments
- 🚀 **CI included** — GitHub Actions runs the suite and publishes the
  live Allure report to GitHub Pages
- 📖 **A written guide** — [docs/qa-automation-guide.html](docs/qa-automation-guide.html),
  explaining every concept the tour teaches by doing (also buildable as
  a small browsable site: `python docs/build_site.py`)

</details>

---

## Supported AI agents

| Agent | How to use |
|---|---|
| Claude Code | Open your scaffolded folder in a terminal — rules in `CLAUDE.md` are picked up automatically |
| Cursor | Copy `CLAUDE.md` to `.cursor/rules/qa-automation.mdc` |
| VS Code Copilot | Copy `CLAUDE.md` to `.github/copilot-instructions.md` |
| Windsurf | Copy `CLAUDE.md` to `.windsurf/rules.md` |
| Any other agent | Paste prompts from `prompts/` and reference `CLAUDE.md` |

---

## Quick start

### 🏁 Learn first (recommended)

Click **Use this template** above (or clone this repo), then:

```bash
pip install -r requirements.txt
playwright install chromium

python tour.py                  # the guided tour (creates tour-tests/)
pytest --headed --slowmo 500    # then watch all 26 tests run
```

You should see a browser window open, run through a test, and close —
26 times in a row — ending with a line like `26 passed in 3m12s`.

(Python 3.10+ required. Only the Allure analytics report additionally
needs Node.js — everything else works without it.)

### 🚀 Test your own app

**A. Fresh project next to the kit:**

```bash
python scaffold.py
```

It asks for a project name, your app's URL, and which framework pieces
you want — **pages** (page objects), **helpers**, **constants**,
**fixtures**, **utils**. Take all of them (recommended), a subset, or
`none` for a bare pytest+Playwright setup; pieces that need each other
are included together automatically. You get an independent project:

```
../my-app-tests/     ← chosen structure, .env filled in, smoke test ready
```

<details>
<summary><strong>Adding tests into an existing repo instead?</strong></summary>

```bash
python scaffold.py --name my-app --url https://... --dest path/to/repo/e2e --into-existing
```

Files you already have are never touched; only missing ones are added.

</details>

**Then, either way:**

```bash
cd ../my-app-tests
pytest tests/test_smoke.py     # proves the toolchain end to end
```

Grow the suite:
- **With an AI agent:** open the folder in your agent and feed it
  `prompts/00-quick-start.md`. The prompts walk it through scanning your
  app, generating baseline tests per page, building e2e journeys, and
  fixing failures — all following the conventions in `CLAUDE.md`.
- **By hand:** in your scaffolded project, copy `pages/example_page.py.template`,
  build your first page object, write tests against it.

---

## Commands cheat sheet

> In the starter kit (learning):

| Command | What it does |
|---|---|
| `python tour.py` | Interactive guided tour |
| `python tour.py --create-tests` | Just (re)create `tour-tests/` and exit |
| `pytest` | Run your copy of the 26 tests (headless) |
| `pytest --headed --slowmo 500` | Watch the browser work (great for learning!) |
| `pytest -k "order"` | Run a group of tests matching a keyword |
| `python run_tests.py` | Run everything + open the Allure report |
| `python scaffold.py` | Create a test project for your own app |

> In your scaffolded project: the same commands, minus the tour.

**Automatic retries:** a failed test is retried up to 2 times before
counting as a real failure (`--reruns` in [pytest.ini](pytest.ini)) —
practice sites and real apps both have slow moments. Retries stay
visible in the reports, so flakiness is never silently hidden.

---

## Folder structure

<details>
<summary><strong>Click to expand the full layout</strong></summary>

```
qa-starter-kit-python/
├── learn/           ← the 26 practice tests (pristine, commented sources)
├── tour-tests/      ← YOUR copy of them (created by the tour, git-ignored)
├── pages/           ← page objects: ALL locators live here, one class per page
├── helpers/         ← reusable user journeys (login, add-to-cart, ...)
├── fixtures/        ← pytest plumbing: ad blocker, screenshots, report labels
├── utils/           ← pure-Python tools (unique test data)
├── constants.py     ← site URL + shared test data
├── conftest.py      ← thin loader that plugs the fixtures in
├── tour.py          ← the interactive learning tour
├── scaffold.py      ← creates a test project for YOUR app
├── template/        ← the generic skeleton the scaffolder copies
├── prompts/         ← copy-paste prompts for AI agents
├── docs/            ← the written guide (qa-automation-guide.html) + its site builder
└── run_tests.py     ← run + build the Allure report in one command
```

Scaffolded projects share the same layered layout (minus the learning
parts). The layering to remember: **tests** (what to verify) →
**helpers** (the journey) → **pages** (where things are). When the app
changes, you fix one locator in one page class — not every test.

</details>

---

## 🤖 How the AI workflow works

1. **Scan** — your agent visits your app's pages and writes a map of
   elements and locators (`prompts/01-scan-pages.md`)
2. **Generate** — it turns the maps into page objects + baseline tests
   (`02-generate-baseline.md`), then full journeys (`03-generate-e2e.md`)
3. **Run** — pytest executes everything, reports with screenshots
4. **Fix** — paste failures into `04-fix-errors.md`; locators get fixed
   in the page objects, never papered over with sleeps
5. **Repeat** — re-scan when your app changes

---

## The 26 practice tests

Every file maps 1-to-1 to an official test case of the practice site and
is commented for beginners. The sources live in [learn/](learn/); the
tour copies them to `tour-tests/` where you run and edit them.

<details>
<summary><strong>Click to see all 26 test cases</strong></summary>

| # | File | What it tests |
|---|------|---------------|
| 1 | [test_tc01_register_user.py](learn/test_tc01_register_user.py) | Register a new user (full flow) |
| 2 | [test_tc02_login_correct.py](learn/test_tc02_login_correct.py) | Login with correct credentials |
| 3 | [test_tc03_login_incorrect.py](learn/test_tc03_login_incorrect.py) | Login with wrong credentials shows error |
| 4 | [test_tc04_logout.py](learn/test_tc04_logout.py) | Logout returns to login page |
| 5 | [test_tc05_register_existing_email.py](learn/test_tc05_register_existing_email.py) | Duplicate email is rejected |
| 6 | [test_tc06_contact_us_form.py](learn/test_tc06_contact_us_form.py) | Contact form + file upload + browser dialog |
| 7 | [test_tc07_test_cases_page.py](learn/test_tc07_test_cases_page.py) | Test Cases page opens |
| 8 | [test_tc08_all_products_and_details.py](learn/test_tc08_all_products_and_details.py) | Product list + product detail page |
| 9 | [test_tc09_search_product.py](learn/test_tc09_search_product.py) | Search products |
| 10 | [test_tc10_subscription_home.py](learn/test_tc10_subscription_home.py) | Footer subscription (home page) |
| 11 | [test_tc11_subscription_cart.py](learn/test_tc11_subscription_cart.py) | Footer subscription (cart page) |
| 12 | [test_tc12_add_products_in_cart.py](learn/test_tc12_add_products_in_cart.py) | Add two products, verify prices/totals |
| 13 | [test_tc13_product_quantity_in_cart.py](learn/test_tc13_product_quantity_in_cart.py) | Quantity 4 shows up in cart |
| 14 | [test_tc14_order_register_while_checkout.py](learn/test_tc14_order_register_while_checkout.py) | Full order — register during checkout |
| 15 | [test_tc15_order_register_before_checkout.py](learn/test_tc15_order_register_before_checkout.py) | Full order — register first |
| 16 | [test_tc16_order_login_before_checkout.py](learn/test_tc16_order_login_before_checkout.py) | Full order — login first |
| 17 | [test_tc17_remove_product_from_cart.py](learn/test_tc17_remove_product_from_cart.py) | Remove product from cart |
| 18 | [test_tc18_view_category_products.py](learn/test_tc18_view_category_products.py) | Category sidebar (Women/Men) |
| 19 | [test_tc19_view_brand_products.py](learn/test_tc19_view_brand_products.py) | Brand pages (Polo/H&M) |
| 20 | [test_tc20_search_and_verify_cart_after_login.py](learn/test_tc20_search_and_verify_cart_after_login.py) | Cart survives logging in |
| 21 | [test_tc21_add_review_on_product.py](learn/test_tc21_add_review_on_product.py) | Submit a product review |
| 22 | [test_tc22_recommended_items.py](learn/test_tc22_recommended_items.py) | Add to cart from carousel |
| 23 | [test_tc23_address_details_in_checkout.py](learn/test_tc23_address_details_in_checkout.py) | Checkout shows registered address |
| 24 | [test_tc24_download_invoice.py](learn/test_tc24_download_invoice.py) | Download invoice after purchase |
| 25 | [test_tc25_scroll_up_with_arrow.py](learn/test_tc25_scroll_up_with_arrow.py) | Scroll-up arrow button |
| 26 | [test_tc26_scroll_up_without_arrow.py](learn/test_tc26_scroll_up_without_arrow.py) | Scroll up with JavaScript |

</details>

Where to start reading:
1. [learn/test_tc01_register_user.py](learn/test_tc01_register_user.py) —
   a full flow written out step by step
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

<details>
<summary><strong>Click to see how CI reporting works</strong></summary>

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

</details>

---

## Key ideas to remember

| Idea | What it means |
|---|---|
| `page` | A browser tab Playwright controls. pytest-playwright gives every test a fresh one automatically. |
| `expect(...)` | A check that *waits automatically* for the condition to become true. You never need `time.sleep()` in Playwright. |
| Locators | Find elements the way a *user* would: `page.get_by_role("link", name="Products")` beats brittle CSS. |
| Arrange, Act, Assert | Prepare what you need, do the action, check the result — the shape of every test. |
| Page objects | All locators in one class per page, so app changes mean one fix, not twenty. |

---

## 🎯 Try these next

Small challenges to build confidence before you touch your own app:

- [ ] In `tour-tests/`, change the search word in test case 9 from
      `"dress"` to `"top"`
- [ ] In test case 13, try a different quantity
- [ ] Add a new test: what happens when you search for something that
      doesn't exist (e.g. `"xyz123"`)?
- [ ] Try Firefox: `pytest --browser firefox` (first:
      `playwright install firefox`)
- [ ] Scaffold a project for a site you use daily and let your AI agent
      build its baseline suite

---

## 🛠️ Troubleshooting

<details>
<summary><strong>"python is not recognized" / "pip is not recognized"</strong></summary>

Python isn't on your PATH. Reinstall from
[python.org](https://www.python.org/downloads/) and tick **"Add
python.exe to PATH"** on the first screen of the installer.

</details>

<details>
<summary><strong>PowerShell says "running scripts is disabled on this system"</strong></summary>

Run this once, then try again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

</details>

<details>
<summary><strong>Tests fail once, then pass on the very next run</strong></summary>

That's expected, not a bug — the practice site (and most real apps) has
slow moments now and then. `pytest.ini` retries a failing test up to 2
times (`--reruns 2`) before calling it a real failure. Retries always
stay visible in the report, so flakiness is never hidden.

</details>

<details>
<summary><strong>A browser never opens, or Playwright complains about missing browsers</strong></summary>

Run `playwright install chromium` (or `playwright install` for all
three engines). Playwright drives its own downloaded copies of the
browsers — not the Chrome/Edge already on your machine.

</details>

<details>
<summary><strong>Where did my results go?</strong></summary>

`reports/report.html` (git-ignored) after every run. Double-click it —
it's a single self-contained file, no server needed.

</details>

---

## 📖 Learn more

- **[docs/qa-automation-guide.html](docs/qa-automation-guide.html)** — a
  from-zero written guide covering every concept the tour teaches
  hands-on: what Playwright is, locators, assertions, fixtures, markers,
  and reports. Open it directly in a browser, or run
  `python docs/build_site.py` for a small browsable multi-page version
  (opens automatically once built).
- [Playwright for Python docs](https://playwright.dev/python/docs/intro)
- [pytest documentation](https://docs.pytest.org/)
