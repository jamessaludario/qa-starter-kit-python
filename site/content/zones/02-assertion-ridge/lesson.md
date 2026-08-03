### The assertion is the test

Everything before it is setup. `expect()` is the line that can fail, and
therefore the line that has value.

### Web-first means it retries

```python
expect(page.get_by_text("Order placed!")).to_be_visible()
```

This does not check once. It keeps re-checking - for up to 5 seconds by
default - until the condition holds or time runs out. A success message
that takes 800 ms to arrive simply passes.

Compare:

```python
assert page.get_by_text("Order placed!").is_visible()   # checks ONCE
```

`is_visible()` answers *"is this true at this exact millisecond?"*. Right
after a click, the answer is usually no, because the page has not caught
up yet. This assert passes on a fast machine and fails on a busy CI
runner. That is the definition of a flaky test, and it is the single
most common bug in beginners' suites.

:::warn Never reach for time.sleep()
A fixed sleep is wrong twice: too short on a slow day, so the test fails
for no reason, and too long on a fast day, so every run pays for it.
`expect()` waits exactly as long as it needs to. If you are tempted to
sleep, there is an `expect()` that says what you were really waiting
for - and this site will not run code containing a sleep, so you may as
well find it now.
:::

### Picking a matcher

| You mean | Write |
|---|---|
| it is on screen | `to_be_visible()` |
| its text is exactly this | `to_have_text("Done")` |
| its text includes this | `to_contain_text("Don")` |
| this input holds this value | `to_have_value("42")` |
| exactly N elements match | `to_have_count(3)` |
| it can be clicked | `to_be_enabled()` |
| a checkbox is ticked | `to_be_checked()` |
| the tab title | `expect(page).to_have_title(...)` |
| the address | `expect(page).to_have_url(...)` |

`to_have_text` compares the **whole** string, so it fails on a card that
also contains a price. `to_contain_text` is the friendlier default when
you only care about part of it.

### Proving something is gone

```python
expect(page.get_by_text("Cart is empty!")).to_be_visible()
expect(page.locator("#product-1")).not_to_be_visible()
expect(page.locator("#cart_info_table tbody tr")).to_have_count(0)
```

Negative assertions retry too - they wait for the thing to *disappear*,
which is exactly what you need after clicking a delete button.

### When a plain assert is right

When you have already read a value into a variable, there is nothing
left to wait for:

```python
names = page.locator(".productinfo p").all_inner_texts()
dresses = [name for name in names if "dress" in name.lower()]
assert len(dresses) > 0, "Expected at least one dress in the results"
```

That is straight out of `learn/test_tc09_search_product.py`, and it is
correct. The rule is not "never assert" - it is **never assert on
something you should have waited for**.

### Reading a failure

```
AssertionError: Locator expected to be visible
Actual value: hidden
Call log:
  - expect(locator).to_be_visible with timeout 5000ms
  - waiting for get_by_text("Order placed!")
```

What was expected, what was found, how long it tried, and what it was
looking for. Four facts, and usually the whole answer.
