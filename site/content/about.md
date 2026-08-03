## About this quest

This is the third track of the
[QA starter kit](https://github.com/jamessaludario/qa-starter-kit-python),
alongside the 26 commented practice tests in `learn/` and the project
scaffolder. It is the browser successor to `python tour.py`.

Everything you write here is **real Playwright**. The import line is the
one the kit's own tests use:

```python
from playwright.sync_api import Page, expect
```

...so a solution you write on this page can be pasted into
`tour-tests/` and run against a real Chromium against the real
[automationexercise.com](https://automationexercise.com) without changing
a character.

## How your Python runs in a browser

Playwright drives real browsers from outside them, so it cannot run
*inside* one. Three pieces stand in for it:

- **AutomationVille**, the shop in the right-hand panel. A static
  look-alike of automationexercise.com with the same ids, class names and
  headings, so your locators transfer.
- **Pyodide**, a real CPython compiled to WebAssembly. Your code is not
  simulated, pattern-matched or faked - it is executed.
- **`playwright_lite`**, a Playwright-shaped shim that drives the shop's
  DOM. It implements auto-waiting, strict mode and Playwright's own error
  messages, because reading those messages is half the skill.

The full design, including what it deliberately does *not* do, is in
`site/ARCHITECTURE.md`.

## How you are marked

Not by comparing your code to ours. Three independent things are checked:

1. **What your test did** - every action it performed on the page.
2. **Where the shop ended up** - its state when your test finished.
3. **How it reads** - an AST review against the kit's conventions
   (no `time.sleep()`, `expect()` where `assert` would be flaky,
   locators kept out of tests).

Find a better locator than ours and you pass. Paste ours with a sleep
bolted on and you do not.

## Privacy

There is no account, no server and no analytics. Progress lives in this
browser's local storage and never leaves the machine. Export it from the
**Progress** page if you want to move it or hand it in.
