# Generate end-to-end journey tests

Copy everything below the line into your AI agent, once the baseline
layer (02) is green.

---

Read `CLAUDE.md` for this project's conventions. The baseline tests
prove pages load; now cover the journeys users actually take.

1. From the page maps and existing page objects, propose the app's
   3-7 most important user journeys (e.g. "sign up -> onboard ->
   see dashboard", "search -> add to cart -> check out"). Show me the
   list and PAUSE for my confirmation before writing code.
2. For each confirmed journey, write `tests/test_e2e_<journey>.py`:
   - the test reads like the user's story: act via page objects and
     helpers, assert the outcome the user would see
   - reusable multi-page sequences go in `helpers/flows.py`
   - tests create their own data (use `utils/data.py` generators) and
     clean up after themselves, so they can run in any order
3. Extend page objects with any missing actions — keep locators out of
   the tests themselves.
4. Run the suite; fix failures with better locators/waits, not sleeps.
5. Finish with a summary of journeys covered and what regression-level
   edge cases you'd test next.
