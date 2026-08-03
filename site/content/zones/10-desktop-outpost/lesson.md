:::warn This zone cannot run here
Every other zone on this map executes your Python against a live DOM.
This one **cannot**, and never will. The whole point of desktop
automation is driving windows that belong to the operating system, and a
web page is not allowed anywhere near them - which is exactly the wall
this zone is about.

So Desktop Outpost is a **read-only lesson and quiz**. To run the real
thing you need Windows, an unlocked desktop, and this repo checked out:

```
pip install -r requirements-desktop.txt
python desktop/run_tests.py
```
:::

## Why Playwright stops at the window frame

Playwright drives **browser engines**. It speaks to Chromium, Firefox
and WebKit through their debugging protocols. A native application's
window is not a web page: there is no DOM, no CSS selector, no
`page.goto()`. No amount of Playwright configuration reaches a desktop
window, so the answer is not a clever locator - it is a different tool.

On Windows, native apps expose their controls through **UI Automation**,
the same accessibility layer that lets a screen reader announce
"button, Login". That layer is what desktop automation tools read, and
it is why they can inspect and click an app's controls without the app
cooperating in any way.

`pywinauto` talks to UI Automation directly, in pure Python, with
nothing extra to run. That is what the kit's `desktop/` folder uses.

## The idea you already have

You have spent this whole quest learning to find elements **by what they
are and what they say** rather than by where they sit in the markup.
`get_by_role("button", name="Login")` is a question asked of the
accessibility tree.

Desktop automation asks the same question of a different tree:

```python
# Web, with Playwright
page.get_by_role("button", name="Equals").click()

# Desktop, with pywinauto
window.child_window(title="Equals", control_type="Button").click_input()
```

Different library, same instinct. If role locators made sense to you,
this will too.

## What you give up outside the browser

Be clear-eyed about the trade, because it is a real one:

- **No auto-waiting.** Playwright's retry loop - the thing Assertion
  Ridge was built around - does not exist here. You wait for a control
  to appear explicitly, and the discipline of *never* reaching for a
  fixed sleep matters more, not less.
- **No headless.** UI Automation drives actual windows, so the screen
  must be logged in and awake. On a locked machine or a disconnected
  remote-desktop session, windows never become visible and everything
  times out. CI needs a dedicated interactive machine.
- **Windows only.** Which is why the kit keeps `pywinauto` in its own
  `requirements-desktop.txt` - so the web tests still install and run on
  macOS and Linux.

## What stays exactly the same

The layering. `desktop/` is deliberately built as a mirror of the web
track: tests assert, helpers run journeys, page objects own every
control. Same architecture, different driver.

That is the real lesson of this outpost. The tool changed and the design
did not - which is a good sign that the design was about testing, not
about Playwright.

:::note The long version
Section 12 of `docs/qa-automation-guide.html` is the full tutorial:
backends, the inspector, waiting strategies, and the finished Calculator
suite.
:::
