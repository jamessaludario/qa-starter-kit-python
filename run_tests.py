"""
run_tests.py
============
One command that does the whole test-and-report routine:

  1. Run the tests with pytest (recording results for both reports)
  2. Carry Allure's history forward, so the TREND graphs build up
     one data point per run (pass rate, duration, retries, ...)
  3. Generate the Allure report
  4. Open the report in your browser

Usage (anything you'd normally give pytest just goes on the end):

  python run_tests.py                                   # all 26 tests
  python run_tests.py --headed                          # watch the browser
  python run_tests.py -k "order"                        # just the order tests
  python run_tests.py tests/test_tc09_search_product.py # one file
  python run_tests.py --no-open                         # don't open browser

Press Ctrl+C in the terminal when you're done looking at the report
(the "allure open" step keeps a little web server running to show it).
"""

import shutil
import subprocess
import sys
from pathlib import Path

# The folders involved. These match --alluredir in pytest.ini.
RESULTS = Path("reports/allure-results")   # raw results, written by pytest
REPORT = Path("reports/allure-report")     # the generated website
HISTORY = REPORT / "history"               # the "memory" the trends need


def main():
    # --no-open is OUR flag (skip step 4); everything else goes to pytest.
    args = [a for a in sys.argv[1:] if a != "--no-open"]
    open_report = "--no-open" not in sys.argv[1:]

    # The Allure CLI is installed by npm as "allure.cmd" on Windows, so we
    # ask Windows where it is instead of hard-coding a path.
    allure = shutil.which("allure")
    if allure is None:
        sys.exit(
            "The 'allure' command was not found.\n"
            "Install it once with:  npm install -g allure-commandline"
        )

    # --- Step 1: run the tests -------------------------------------------
    # (sys.executable = the python running this script, so the tests run
    # with the same Python/packages no matter how many you have installed)
    print(">> Running tests...")
    test_run = subprocess.run([sys.executable, "-m", "pytest", *args])

    # Exit code 0 = all passed, 1 = some failed. Both produce results we
    # want to see! Anything else (2+) means pytest itself had a problem
    # (bad arguments, interrupted, ...), so there is nothing to report.
    if test_run.returncode not in (0, 1):
        sys.exit(test_run.returncode)

    # --- Step 2: carry the history forward -------------------------------
    # Each report's history/ folder is the accumulated record of past runs.
    # Copying it into the new results BEFORE generating is what makes the
    # "Trend" graphs show more than one run.
    if HISTORY.exists():
        print(">> Carrying report history forward (for the trend graphs)...")
        shutil.copytree(HISTORY, RESULTS / "history", dirs_exist_ok=True)

    # --- Step 3: generate the report --------------------------------------
    print(">> Generating the Allure report...")
    subprocess.run(
        [allure, "generate", str(RESULTS), "-o", str(REPORT), "--clean"],
        check=True,
    )

    # --- Step 4: open it in the browser ------------------------------------
    if open_report:
        print(">> Opening the report (press Ctrl+C here when done)...")
        subprocess.run([allure, "open", str(REPORT)])

    # Report the test outcome as our own exit code, so this script can be
    # used in CI too (0 = green, 1 = something failed).
    sys.exit(test_run.returncode)


if __name__ == "__main__":
    main()
