"""
tour.py - an interactive learning tour of this automation kit
==============================================================
Run it with:

    python tour.py

No arguments, no setup beyond the kit's own install steps. The tour is a
menu of short chapters. Read a little, then WATCH a real browser do the
work - every "watch" chapter opens Chromium in slow motion so you can see
exactly what the test script is doing, step by step.

Chapters can be taken in any order, but first-timers should just go 1-2-3...
"""

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

# Everything the tour launches (pytest, playwright) is run with THIS python,
# so it always uses the same packages you installed for the kit.
PY = sys.executable

LINE = "-" * 72


def say(text):
    """
    Print tour text nicely: normal paragraphs get wrapped to 72 chars,
    while indented blocks (lists, code samples) are printed exactly as
    written so their layout survives.
    """
    for block in textwrap.dedent(text).strip("\n").split("\n\n"):
        if any(line.startswith((" ", "\t")) for line in block.splitlines()):
            print(block)  # preformatted: keep the indentation
        else:
            print(textwrap.fill(" ".join(block.split()), width=72))
        print()


def pause(prompt="  [Enter] to continue... "):
    try:
        input(prompt)
    except EOFError:        # piped input ran out - just keep going
        print()
    print()


def run(args):
    """Run a command, showing it first so learners connect action to command."""
    print(">>", " ".join(args))
    print(LINE)
    result = subprocess.run(args)
    print(LINE)
    return result


# ---------------------------------------------------------------------------
# Chapter 1 - welcome
# ---------------------------------------------------------------------------

def chapter_welcome():
    say("""
        CHAPTER 1 - WHAT IS THIS KIT?

        Test automation means writing a program that uses a website the
        way a person would - clicking buttons, filling forms, reading the
        page - and CHECKS that the site behaves correctly. Instead of a
        human re-testing everything after each change, the scripts do it
        in minutes.

        This kit tests a site built exactly for practicing:
        https://automationexercise.com. It publishes 26 official test
        cases, and this kit implements every one of them with Playwright
        (the tool that drives the browser) and pytest (the tool that runs
        tests and reports results).

        Your map of the kit:

          tests/            one file per test case, heavily commented
          pages/            "page objects" - one class per page of the site
          helpers/          user journeys like create_account()
          pytest.ini        settings applied to every run
          run_tests.py      run everything + build a graphical report
          README.md         the written version of this tour

        Where to start reading: tests/test_tc01_register_user.py - it
        walks through a full user registration one commented step at a
        time. But before reading anything, take Chapter 2 and WATCH a
        test run. It makes everything else click.
    """)
    pause()


# ---------------------------------------------------------------------------
# Chapter 2 - watch a test run
# ---------------------------------------------------------------------------

def chapter_watch():
    say("""
        CHAPTER 2 - WATCH YOUR FIRST TEST RUN

        A browser window is about to open BY ITSELF and search the shop
        for a dress, like a very fast, very obedient intern. The test is
        tests/test_tc09_search_product.py, slowed down (500 ms between
        actions) so your eyes can follow.

        Watch for these moments:

          1. The home page opens (and a cookie popup gets dismissed)
          2. It clicks 'Products' in the menu
          3. It types "dress" into the search box and hits the button
          4. It CHECKS the results - every product shown must actually
             be a dress. That check is the entire point of a test.

        The window closes on its own when the test finishes.
    """)
    pause("  [Enter] to launch the browser... ")
    run([PY, "-m", "pytest", "tests/test_tc09_search_product.py",
         "--headed", "--slowmo", "500", "--reruns", "0"])
    say("""
        That '1 passed' at the bottom is the verdict. Now open
        tests/test_tc09_search_product.py in your editor and read it -
        you have already SEEN every line of it happen, so the code will
        feel familiar. This watch-then-read order works for any test in
        the kit:

            python -m pytest tests/<any test file> --headed --slowmo 500
    """)
    pause()


# ---------------------------------------------------------------------------
# Chapter 3 - how tests find things
# ---------------------------------------------------------------------------

def chapter_locators():
    say("""
        CHAPTER 3 - LOCATORS: HOW TESTS FIND THINGS ON A PAGE

        Before a script can click a button, it must FIND the button.
        The finding recipe is called a locator. The golden rule: locate
        things the way a USER would describe them, not by their position.

        The kit uses these, from best to most technical:

          page.get_by_role("link", name="Products")
              "the link that says Products" - how a user thinks. Survives
              redesigns as long as the link still says Products.

          page.get_by_text("Account Created!")
              "wherever it says Account Created!" - great for checking
              that a message appeared.

          page.locator("#search_product")
              CSS id. Precise but technical - the id can change even
              when the page looks identical.

          page.locator('input[data-qa="login-email"]')
              An attribute developers add SPECIFICALLY for tests. When a
              site offers these (this one does), use them - they are a
              promise that tests may rely on them.

        And the check side - every test ends with an expectation:

          expect(page.get_by_text("Logged in as Bob")).to_be_visible()

        expect() WAITS (up to a timeout) for the condition to come true.
        That patience is why Playwright tests never need sleep() calls
        sprinkled around - and unexplained sleeps are the #1 smell in
        beginner test code.

        See them in action: the page classes in the pages/ folder use
        all four styles, with comments saying why each was chosen.
    """)
    pause()


# ---------------------------------------------------------------------------
# Chapter 4 - record your own script by clicking
# ---------------------------------------------------------------------------

def chapter_codegen():
    say("""
        CHAPTER 4 - RECORD A SCRIPT BY CLICKING (CODEGEN)

        Playwright has a magic trick: it can WATCH YOU use a site and
        WRITE THE CODE for you. Two windows will open - the website, and
        an inspector that fills with Python as you click.

        Try this while it runs:

          1. Click around: open Products, search for something, view an
             item. Watch a line of code appear for every action.
          2. Hover anything - codegen shows the locator it would use,
             teaching you Chapter 3 interactively.
          3. Copy the generated code from the inspector window if you
             want to keep it (it makes a great skeleton for a test).

        Recorded code is a starting point, not a finished test: it has
        clicks but no CHECKS. A real test adds expect() lines - the
        difference between "do stuff" and "verify the site works".

        Close both windows when you're done to come back to the menu.
    """)
    pause("  [Enter] to start recording... ")
    run([PY, "-m", "playwright", "codegen",
         "--target", "python-pytest", "https://automationexercise.com"])
    print()


# ---------------------------------------------------------------------------
# Chapter 5 - write your first test
# ---------------------------------------------------------------------------

FIRST_TEST = Path("tests/test_my_first_test.py")

FIRST_TEST_TEMPLATE = '''\
"""
My first test! Created by the learning tour (tour.py, Chapter 5).

It already passes. Your mission: make it YOURS by finishing the TODOs.
Run it (and watch it!) with:

    python -m pytest tests/test_my_first_test.py --headed --slowmo 500
"""

from playwright.sync_api import Page, expect

from helpers.flows import open_page


def test_my_first_test(page: Page):
    # Step 1: open the home page (helper from helpers/flows.py - it also
    # closes the cookie popup for you).
    open_page(page)

    # Step 2: a check that already works - the site's headline is shown.
    expect(page.get_by_role("heading", name="AutomationExercise")).to_be_visible()

    # TODO 1: click 'Products' in the top menu. Chapter 3 says the best
    # locator is by role and name:
    #   page.get_by_role("link", name=" Products").click()
    # (the leading space is really in the link's text - try it, then use
    # codegen or your browser's inspector to see why!)

    # TODO 2: check you actually arrived - the products page shows the
    # text "All Products". Write an expect() for it.

    # TODO 3 (stretch): search for "top" using the search box
    # (page.locator("#search_product")) and check the results appear.
'''


def chapter_first_test():
    say("""
        CHAPTER 5 - WRITE YOUR FIRST TEST

        Time to switch from passenger to driver. The tour will create
        tests/test_my_first_test.py - a working test with three TODOs
        that grow it from "opens the page" into a real user journey.
    """)
    if FIRST_TEST.exists():
        say("(tests/test_my_first_test.py already exists - keeping your "
            "version, not overwriting it.)")
    else:
        FIRST_TEST.write_text(FIRST_TEST_TEMPLATE, encoding="utf-8")
        say("Created tests/test_my_first_test.py.")
    say("""
        The loop that all test-writing follows:

          1. Edit the file (do one TODO)
          2. Watch it:  python -m pytest tests/test_my_first_test.py
                        --headed --slowmo 500
          3. Green? Next TODO. Red? Read the error - Playwright's
             failure messages tell you exactly what it looked for and
             what it found instead.

        Shall the tour run your test right now so you see it pass?
    """)
    answer = input("  Run it? [y/N] ").strip().lower()
    print()
    if answer == "y":
        run([PY, "-m", "pytest", str(FIRST_TEST),
             "--headed", "--slowmo", "500", "--reruns", "0"])
    pause()


# ---------------------------------------------------------------------------
# Chapter 6 - reports
# ---------------------------------------------------------------------------

def chapter_reports():
    say("""
        CHAPTER 6 - REPORTS: THE RESULTS, MADE VISIBLE

        Every run of this kit records results two ways:

          reports/report.html
              One self-contained page: every test, pass/fail, timings,
              and full error details. Open it by double-clicking.

          The Allure report (graphs & analytics)
              An interactive dashboard: pass-rate donut, duration
              charts, failure screenshots, and trend graphs that grow
              with every run. One command does everything:

                  python run_tests.py

              (Needs the free Allure CLI once: npm install -g
              allure-commandline - see README for details.)

        Reports turn "the tests ran" into something you can SHOW -
        a teammate, a manager, or your future self wondering when a
        test started failing. This kit even publishes its own report
        to the web automatically on every push (see the CI section of
        the README when you're ready for that level).

        A taste right now (about 30 seconds): run two quick tests, then
        open report.html to see them listed.
    """)
    answer = input("  Run the two tests? [y/N] ").strip().lower()
    print()
    if answer == "y":
        run([PY, "-m", "pytest", "tests/test_tc07_test_cases_page.py",
             "tests/test_tc10_subscription_home.py"])
        say("""
            Done - now open reports/report.html in your browser
            (double-click it in your file explorer) and find the two
            tests you just ran.
        """)
    pause()


# ---------------------------------------------------------------------------
# The menu
# ---------------------------------------------------------------------------

CHAPTERS = [
    ("What is this kit?  (start here)", chapter_welcome),
    ("Watch your first test run  (opens a browser!)", chapter_watch),
    ("Locators - how tests find things", chapter_locators),
    ("Record a script by clicking  (opens a browser!)", chapter_codegen),
    ("Write your first test", chapter_first_test),
    ("Reports - see and share the results", chapter_reports),
]


def check_setup():
    """A friendly nudge if the kit's install steps were skipped."""
    try:
        import playwright  # noqa: F401
        import pytest      # noqa: F401
    except ImportError:
        say("""
            One-time setup needed first! In this folder, run:

                pip install -r requirements.txt
                playwright install chromium

            ...then start the tour again with: python tour.py
        """)
        sys.exit(1)


def main():
    check_setup()
    print()
    print("  WELCOME TO THE AUTOMATION LEARNING TOUR")
    print("  (Playwright + Python, using automationexercise.com)")
    while True:
        print()
        for number, (title, _) in enumerate(CHAPTERS, start=1):
            print(f"   {number}. {title}")
        print("   q. Quit the tour")
        print()
        try:
            raw = input("  Pick a chapter: ")
        except EOFError:
            break
        # Menu answers are only ever plain digits or letters, so keep
        # just those - this quietly drops the junk characters some
        # Windows shells add in front of piped input.
        choice = "".join(
            ch for ch in raw if ch.isascii() and ch.isalnum()
        ).lower()
        print()
        if choice == "q":
            break
        if choice.isdigit() and 1 <= int(choice) <= len(CHAPTERS):
            CHAPTERS[int(choice) - 1][1]()
        else:
            print("  (Type a chapter number, or q to quit.)")
    say("""
        Happy testing! Next steps whenever you're ready: read the tests
        in numbered order, do the 'Ideas to try next' in the README, and
        break things on purpose - a red test you understand teaches more
        than a green one you don't.
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Tour closed. Run 'python tour.py' anytime to continue!")
