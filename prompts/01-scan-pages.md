# Scan the app's pages

Copy everything below the line into your AI agent, opened in your test
project folder. Use this when starting out, and again whenever the app
has changed (re-scan).

---

Read `CLAUDE.md` for this project's conventions, then map the app under
test (BASE_URL in `constants.py`, loaded from `.env`).

1. Visit the app's pages, starting from BASE_URL and following its own
   navigation. If you have a browser tool, use it; otherwise write a
   temporary Playwright Python script that visits each page and prints
   the accessibility-relevant elements (roles, names, headings, forms).
2. For every distinct page, write `page-maps/<page-name>.md` containing:
   - path (relative to BASE_URL) and what the page is for
   - key elements a user interacts with, each with the locator you'd
     use — prefer `get_by_role(name=...)`, then labels/test-ids, CSS
     only as a last resort
   - any state needed to reach it (logged in? a record must exist?)
3. Do not write any page objects or tests yet.
4. Finish by listing the pages found, flagging any you could NOT reach
   (login-protected, error, ...) so I can provide credentials or steps.
