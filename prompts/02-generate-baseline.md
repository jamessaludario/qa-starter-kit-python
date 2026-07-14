# Generate baseline tests

Copy everything below the line into your AI agent, after the scan
prompt (01) has produced `page-maps/`.

---

Read `CLAUDE.md` for this project's conventions. Using the page notes in
`page-maps/`, generate the BASELINE layer of the suite: for every page,
prove it loads and shows its key elements.

1. For each mapped page, create a page object `pages/<name>_page.py`:
   - class inherits `BasePage`, sets `path`
   - one method per user action, one `expect_loaded()` check method
   - ALL locators live here, taken from the page map
   - export the class from `pages/__init__.py`
2. For each page object, create `tests/test_baseline_<name>.py` with a
   test that opens the page and asserts its key elements are visible.
   Assertions in the test, locators in the page object.
3. If several pages need the same journey to reach them (e.g. login),
   add ONE helper to `helpers/flows.py` and reuse it.
4. Add the app's areas to `FEATURE_AREAS` in `fixtures/reporting.py`
   so the Allure report groups results per area.
5. Run `python -m pytest --reruns 0`. Fix failures by correcting
   locators or expect()-based waits — never sleeps, never retries.
6. Finish with a coverage summary: page -> page object -> test file.
