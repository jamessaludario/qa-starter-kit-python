"""
desktop/run_tests.py
=====================
Running the desktop tests directly with pytest means remembering two
flags every time (see desktop/tests/test_calculator.py for why:
--confcutdir keeps the web track's browser fixtures out of these tests,
--reruns 0 turns off the web track's retry-on-failure). This script
bakes both in, the way run_tests.py (repo root) bakes in the Allure
report steps for the web track.

Usage (anything you'd normally give pytest just goes on the end):

  python desktop/run_tests.py                            # everything
  python desktop/run_tests.py -k "add"                   # matching tests
  python desktop/run_tests.py desktop/tests/test_calculator.py
"""

import subprocess
import sys
from pathlib import Path

DESKTOP_DIR = Path(__file__).parent
TESTS_DIR = DESKTOP_DIR / "tests"


def main():
    args = sys.argv[1:]

    # If the caller already pointed pytest at a specific file/folder, use
    # that. Otherwise default to running every desktop test.
    #
    # Checking .exists() (not just "doesn't start with -") matters because
    # some flags take a bare value of their own, like -k "add" - "add"
    # isn't a path, so a plain not-a-dash check would wrongly skip our
    # default and let pytest fall back to its own testpaths (tour-tests).
    pointed_at_a_path = any(
        not arg.startswith("-") and Path(arg).exists() for arg in args
    )
    default_target = [] if pointed_at_a_path else [str(TESTS_DIR)]

    command = [
        sys.executable, "-m", "pytest",
        f"--confcutdir={DESKTOP_DIR}",
        "--reruns", "0",
        *default_target,
        *args,
    ]
    print(">> Running desktop tests...")
    # check=False: a failing test makes pytest exit non-zero, and that is a
    # result to pass on (see below), not an exception to crash on.
    result = subprocess.run(command, check=False)

    # Same exit code pytest gave us, so this script works in CI too.
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
