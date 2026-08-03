### A locator is an address, not a search result

```python
# Nothing happens yet. This is just the address.
login_button = page.get_by_role("button", name="Login")

# NOW Playwright goes and finds it.
login_button.click()
```

Locators are **lazy** and **self-updating**: every action re-finds the
element from scratch. That is why a locator keeps working on a page that
redraws itself, and why you can build one before the element exists.

### The priority order

Not all addresses age equally well. Work down this list and stop at the
first one that fits:

1. `get_by_role()` - what the element **is** plus what it **says**
2. the other `get_by_*` methods - label, placeholder, text, alt text
3. `get_by_test_id()` - a `data-testid` the developers added for you
4. simple CSS - `#search_product`, `.productinfo`
5. XPath - last resort

The reason is not taste. The top of the list describes the page the way
a **user** perceives it, and that changes far less often than the HTML
underneath it. A `div.col-sm-4 > div:nth-child(2) > a` breaks the day
somebody adds a wrapper. "The link called Cart" does not.

:::note What get_by_role actually matches
The **role** is what the element is: `button`, `link`, `heading`,
`checkbox`, `textbox`. The **name** is its accessible name - usually its
visible text, or an `aria-label`, or the `<label>` tied to an input.
Matching is case-insensitive and matches a substring, so
`name="Cart"` also matches a link that says "View Cart". That bites
people, and it is Challenge 3.
:::

### When several things match: strict mode

```python
page.get_by_role("link", name="Test Cases").click()
# Error: strict mode violation: ... resolved to 2 elements
```

Playwright will not guess. Two matches is an error, immediately - no
retry, because retrying cannot help. You have three ways out, best
first:

```python
# 1. Scope it: search inside the part of the page you meant
page.locator(".shop-menu").get_by_role("link", name="Cart").click()

# 2. Filter it: keep only matches containing some text
page.locator(".productinfo").filter(has_text="Blue Top")

# 3. Index it: pick by position - correct, but brittle
page.get_by_role("link", name="Test Cases").first
```

`.first` is not shameful; `learn/test_tc07_test_cases_page.py` uses it
and says why in a comment. But reach for it *after* you have decided
that position is genuinely the thing you mean.

### Actionability: why a click can time out on a visible element

Before Playwright clicks, it checks the element is visible, enabled, and
that nothing is on top of it. If a cookie banner is covering your
button, you get:

```
- <div class="consent-popup"> intercepts pointer events
- retrying click action
```

That is Playwright refusing to do something a real user could not do. It
is a feature, and it is the reason `pages/base_page.py` in the kit
dismisses the consent popup before doing anything else.

### Chaining

```python
# Search INSIDE another element
page.locator("#cartModal").get_by_role("button", name="Continue Shopping")

# Keep only matches that contain some text
page.get_by_role("listitem").filter(has_text="Blue Top")

# Position, counting from zero
page.locator(".productinfo").nth(2)
```

Chaining is the tool you should reach for most, because it says
something true about the page: *this button, the one inside the modal*.
