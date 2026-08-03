### A test is a script that can fail

Automation means writing a program that uses a website the way a person
would - clicking, typing, reading - and then **checks** that the site
behaved. The check is the whole point. A script with no check can run
green forever while the site is on fire.

That check is called an **assertion**, and in Playwright it looks like
this:

```python
expect(page.get_by_text("Order placed!")).to_be_visible()
```

### Two tools, two jobs

- **Playwright** drives the browser: `goto`, `click`, `fill`.
- **pytest** finds your tests, runs them, and tells you which failed.

They meet in one line you will write at the top of every file:

```python
from playwright.sync_api import Page, expect
```

`page` is a fresh browser tab, handed to your test automatically. You
never create it yourself.

### pytest only collects things named `test_`

This is a discovery rule, not a style preference:

- files must be named `test_*.py`
- functions inside them must be named `test_*`

Anything else is silently ignored - which is why "my test does not run"
is almost always "my test is not called `test_something`".

### Arrange, Act, Assert

Nearly every good test has the same three beats:

1. **Arrange** - get ready: open the page, set up the data you need.
2. **Act** - do the one thing you are testing.
3. **Assert** - check the outcome.

```python
def test_search_finds_dresses(page: Page):
    page.goto("https://automationexercise.com/products")   # Arrange
    page.locator("#search_product").fill("dress")          # Act
    page.locator("#submit_search").click()                 # Act
    expect(page.get_by_role(                               # Assert
        "heading", name="Searched Products")).to_be_visible()
```

If your assert comes before your act, you are testing the page you
started on. That mistake is Challenge 3.

:::tip One behaviour per test
`test_login_with_wrong_password_shows_error` is one test. Do not also
check the signup form in it. When it fails, its name should tell you
what broke before you open the file.
:::

### About the shop on the right

It is a stand-in for [automationexercise.com](https://automationexercise.com)
with the same ids, class names and headings. Anything you learn here
points at the real thing.

One difference worth knowing: it has **no real clock**. Slow operations
happen on a virtual timeline that only moves while `expect()` is
waiting. That is not a cheat - it means "the results take 600 ms to
arrive" is exactly reproducible, so auto-waiting can be taught honestly
instead of hopefully.
