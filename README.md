# Playwright + Python — Beginner Automation Tests

Beginner-friendly automated tests for the practice website
[automationexercise.com](https://automationexercise.com), covering **all 26
official test cases** from its [test cases page](https://automationexercise.com/test_cases).

Every test file is heavily commented and maps 1-to-1 to a test case on the
site: `test_tc09_...` is the site's "Test Case 9", and the numbered comments
inside follow the site's official steps.

**New to test automation? Take the guided tour first:**

```bash
python tour.py
```

An interactive, menu-driven tour ([tour.py](tour.py)) that teaches by
*showing*: it opens a real browser so you can watch a test drive the
site in slow motion, lets you record your own script just by clicking
around (Playwright's codegen), creates a starter test with guided
TODOs for you to finish, and walks you through the reports. Take the
chapters in order the first time; revisit any chapter any time.

## Sharing this kit

Everything is self-contained — to hand this to a colleague or student,
just share the repository link. Their complete setup is:

```bash
git clone https://github.com/jamessaludario/sample-playwright-python.git
cd sample-playwright-python
pip install -r requirements.txt
playwright install chromium
python tour.py
```

(Python 3.10+ required. The Allure report additionally needs Node.js —
see the Test reports section — but everything else, including the tour
and the quick HTML report, works without it.)

## How the kit is organized

The layout mirrors how professional UI test suites are structured —
each kind of thing has its own home:

| Where | What lives there |
|---|---|
| [tests/](tests/) | The test cases — WHAT to verify |
| [helpers/](helpers/flows.py) | User journeys (`create_account`, ...) that many tests reuse |
| [pages/](pages/) | Page objects — one class per page of the site, holding its locators and actions |
| [constants.py](constants.py) | Shared data: site URL, account details, the fake card |
| [fixtures/](fixtures/) | Things pytest runs around every test: ad blocker, failure screenshots, report labels |
| [utils/](utils/data.py) | Small standalone tools like `unique_email()` |
| [conftest.py](conftest.py) | A thin loader that plugs the fixtures in |

The layering to remember:
**tests** (what to verify) → **helpers** (the journey) → **pages**
(where things are on each page) → the browser. When the site changes,
you fix one locator in one page class — not 26 tests.

## Where to start reading

1. **[test_tc01_register_user.py](tests/test_tc01_register_user.py)** — the
   full registration flow written out step by step. Later tests reuse the
   `create_account()` helper instead of repeating it.
2. **[helpers/flows.py](helpers/flows.py)** then
   **[pages/base_page.py](pages/base_page.py)** — see how a helper like
   `create_account()` is built from page-object methods.
3. Then browse by topic below.

## The 26 test cases

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

Good stuff to know:
- Tests that need an account **create their own throwaway account**
  (unique email each run) and **delete it at the end** — every test is
  self-contained and can run alone, in any order.
- The order tests (14, 15, 16, 24) pay with an obviously **fake card
  number** — this is a practice site, no real payment happens.

## One-time setup

```bash
# 1. Install the Python packages
pip install -r requirements.txt

# 2. Download the browser Playwright will control
playwright install chromium
```

## Running the tests

```bash
# Run all 26 tests (browser is hidden / "headless")
pytest

# Run all tests and WATCH the browser do its thing (great for learning!)
pytest --headed

# Watch in slow motion (500 ms pause between each action)
pytest --headed --slowmo 500

# Run just one test case
pytest tests/test_tc09_search_product.py

# Run a group (e.g. all three checkout flows)
pytest -k "order"

# Show the print() output from the tests
pytest -s
```

**Automatic retries:** the practice site is sometimes slow or flaky, so
a test that fails is automatically retried up to 2 times (with a 2-second
pause) before being reported as a real failure — see `--reruns` in
[pytest.ini](pytest.ini). Retried tests are counted under "Reruns" in the
HTML report and "Retries" in Allure, so genuine flakiness stays visible
instead of being silently hidden.

## Test reports

Every run automatically produces **two** kinds of results in the
(git-ignored) `reports/` folder:

### 1. Quick HTML report (pytest-html)

`reports/report.html` — a single self-contained file with a pass/fail
summary, one row per test, durations, and full error details for
failures. Open it by double-clicking the file, or right-click →
"Reveal in File Explorer" → open with Chrome/Edge.

> **Why pytest-html is pinned to 3.x:** version 4+ fills in the results
> table with JavaScript, so the report looks empty in viewers that block
> scripts (some IDE previews, locked-down browsers). 3.x writes the
> results as plain HTML that displays anywhere.

### 2. Graphs & analytics (Allure)

Each run also records raw results into `reports/allure-results`. Turn
them into an interactive dashboard — status pie chart, duration graphs,
a timeline, severity breakdowns, and pass-rate **trends across runs**:

```bash
# One-time setup (needs Node.js; the CLI itself runs on Java 8+)
npm install -g allure-commandline
```

The easiest way to use it is **[run_tests.py](run_tests.py)** — one
command that runs the tests, carries the trend history forward,
generates the report, and opens it in your browser:

```bash
python run_tests.py                 # all tests + report
python run_tests.py --headed       # any pytest option works
python run_tests.py -k "order"     # ...including picking tests
python run_tests.py --no-open      # skip opening the browser
```

Run it repeatedly and the **Trend** graphs (pass rate, duration,
retries per run) build up one data point per run — that history
carry-over is exactly what the script automates for you.

Prefer doing it by hand? `allure serve reports/allure-results` after a
plain `pytest` run shows the same report (just without trends). Either
way, Allure's report is served over a local web server — don't open
its index.html directly from the file system, it won't load that way.

### Reports in CI (GitHub Actions)

[.github/workflows/tests.yml](.github/workflows/tests.yml) runs the
suite on every push to `main` (or manually from the Actions tab) and
delivers the reports two ways:

- **Live Allure report on GitHub Pages** — every run publishes to
  <https://jamessaludario.github.io/sample-playwright-python/>, with
  history carried between runs so the trend graphs grow in CI too.
- **Downloadable artifact** — each run attaches `test-reports`
  (the self-contained `report.html` plus the Allure folder) under
  the run's summary page.

The workflow still turns red when tests fail — the report is
generated and published *first*, then the real test result is
reported, so a red run always has its report attached.

## Key ideas to remember

- **`page`** — a browser tab Playwright controls. pytest-playwright gives
  every test a fresh one automatically.
- **`expect(...)`** — a check that *waits automatically* for the condition
  to become true. You never need `time.sleep()` in Playwright.
- **Locators** — ways to find elements on a page:
  - `page.get_by_role("link", name="Products")` — by what users see (best!)
  - `page.locator("#search_product")` — by CSS id
  - `page.locator(".productinfo")` — by CSS class
  - `page.locator('input[data-qa="login-email"]')` — by attribute
- **A test = Arrange, Act, Assert** — prepare what you need, do the action,
  check the result.
- **Self-contained tests** — a good test creates whatever it needs
  (accounts, cart items) and cleans up after itself.

## Ideas to try next

1. Change the search word in test case 9 from `"dress"` to `"top"`.
2. In test case 13, try a different quantity.
3. Add a new test: sort out what happens when you search for something
   that doesn't exist (e.g. `"xyz123"`).
4. Try running against Firefox: `pytest --browser firefox`
   (first run `playwright install firefox`).
