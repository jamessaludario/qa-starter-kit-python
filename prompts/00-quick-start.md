# Quick start — from empty scaffold to passing test suite

Copy everything below the line into your AI agent, opened in your
scaffolded test project folder.

---

You are working in a Playwright + Python (pytest) test project scaffolded
from qa-starter-kit-python. Read `CLAUDE.md` first — it defines the
architecture and conventions you must follow.

Then do the following, in order:

1. Read `constants.py` to find the app under test (BASE_URL from `.env`).
2. Run the smoke test to prove the toolchain works:
   `python -m pytest tests/test_smoke.py --reruns 0`
   If it fails, fix the environment problem before writing any tests.
3. Explore the app: write a short throwaway Playwright script (or use
   your browser tool if you have one) to visit the app's main pages
   starting from BASE_URL. For each page note its path, purpose, and
   key elements with the locators you'd use (prefer get_by_role).
   Save your notes as one markdown file per page in `page-maps/`.
4. Show me the list of pages you found and PAUSE — let me confirm which
   ones matter before generating anything.
5. After I confirm: for each confirmed page, create a page object in
   `pages/` and a baseline test in `tests/` that opens the page and
   checks its key elements are visible.
6. Run the suite (`python -m pytest --reruns 0`), fix any failures by
   correcting locators/waits (never with sleeps), and repeat until green.
7. Finish with a summary: pages covered, tests created, anything you
   noticed about the app that deserves deeper testing next.
