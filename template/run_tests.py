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

  python run_tests.py                     # all tests
  python run_tests.py --headed            # watch the browser
  python run_tests.py -k "login"          # just tests matching a word
  python run_tests.py --no-open           # don't open the browser

Press Ctrl+C in the terminal when you're done looking at the report
(the "allure open" step keeps a little web server running to show it).
"""

import shutil
import subprocess
import sys
from pathlib import Path

from constants import PROJECT_NAME

# The folders involved. These match --alluredir in pytest.ini.
RESULTS = Path("reports/allure-results")   # raw results, written by pytest
REPORT = Path("reports/allure-report")     # the generated website
HISTORY = REPORT / "history"               # the "memory" the trends need

# The title shown at the top of the report's Overview page.
REPORT_NAME = f"{PROJECT_NAME} Test Report"


def main():
    # --no-open is OUR flag (skip step 4); everything else goes to pytest.
    args = [a for a in sys.argv[1:] if a != "--no-open"]
    open_report = "--no-open" not in sys.argv[1:]

    # The Allure CLI is installed by npm; ask the system where it is.
    allure = shutil.which("allure")
    if allure is None:
        sys.exit(
            "The 'allure' command was not found.\n"
            "Install it once with:  npm install -g allure-commandline"
        )

    # --- Step 1: run the tests -------------------------------------------
    print(">> Running tests...")
    test_run = subprocess.run([sys.executable, "-m", "pytest", *args])

    # Exit code 0 = all passed, 1 = some failed. Both produce results we
    # want to see! Anything else (2+) means pytest itself had a problem.
    if test_run.returncode not in (0, 1):
        sys.exit(test_run.returncode)

    # --- Step 2: carry the history forward -------------------------------
    if HISTORY.exists():
        print(">> Carrying report history forward (for the trend graphs)...")
        shutil.copytree(HISTORY, RESULTS / "history", dirs_exist_ok=True)

    # --- Step 3: generate the report --------------------------------------
    print(">> Generating the Allure report...")
    subprocess.run(
        [allure, "generate", str(RESULTS), "-o", str(REPORT), "--clean",
         "--report-name", REPORT_NAME],
        check=True,
    )

    # --- Step 4: open it in the browser ------------------------------------
    if open_report:
        print(">> Opening the report (press Ctrl+C here when done)...")
        subprocess.run([allure, "open", str(REPORT)])

    sys.exit(test_run.returncode)


if __name__ == "__main__":
    main()
