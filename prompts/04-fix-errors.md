# Fix failing tests

Copy everything below the line into your AI agent, followed by the
failing output.

---

Read `CLAUDE.md` for this project's conventions. Some tests are failing;
the pytest output is pasted below.

1. Reproduce each failure first: run the single failing test with
   `python -m pytest <test file> --reruns 0`. Check the failure
   screenshot in the Allure results (`reports/allure-results/*.png`)
   before theorizing.
2. Diagnose the true cause. The usual suspects, in order:
   - locator drift: the app changed; update the PAGE OBJECT, not the test
   - timing: something needed an `expect()` wait that isn't there
   - test pollution: the test depends on data another test changed —
     make it create its own data
   - real app bug: the app misbehaves — do NOT paper over it; report it
3. Forbidden fixes: `time.sleep()`, raising retry counts, deleting or
   skipping the test, loosening an assertion until it can't fail.
4. Rerun after each fix until the suite is green.
5. Finish with a table: test -> root cause -> fix (or "app bug" with
   reproduction steps I can file).

Failing output:

```
<paste your pytest output here>
```
