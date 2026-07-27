"""
desktop/pages/base_app.py
==========================
The parent class every desktop page object inherits from. It plays the
same role BasePage (pages/base_page.py) plays for the web track: launch
"your" app and hand back its main window, so the child class can get
straight to describing controls.

Launching a modern Windows app reliably is fiddlier than it looks, and
open() below works around three traps. Each one caused a real, confusing
failure while this kit was written, so each is explained where it happens.
"""

from typing import ClassVar

from pywinauto.application import Application
from pywinauto.findwindows import find_elements
from pywinauto.timings import TimeoutError as WaitTimeoutError
from pywinauto.timings import wait_until_passes

# How long to wait for a window, and for the UI inside it, before giving up.
WAIT_TIMEOUT = 15

# How often to re-check while waiting. Polling beats sleeping: we continue
# the instant the condition is true instead of always paying a fixed cost.
RETRY_INTERVAL = 0.3


class BaseApp:
    # Child classes (CalculatorPage, ...) override these with "their"
    # app's launch command and window title, the same way LoginPage
    # overrides BasePage.path.
    app_path = None
    window_title = None

    # child_window() keywords for ONE control that only exists once the
    # app's UI has really loaded - see TRAP 3. Set it in the child class;
    # leave it None to skip the check.
    ready_control: ClassVar[dict | None] = None

    def __init__(self):
        self.app = None
        self.window = None

    def _matching_elements(self):
        """Every top-level element currently showing our window title."""
        return find_elements(
            title=self.window_title, backend="uia", top_level_only=True
        )

    def open(self):
        """
        Launch the app and bind to the window WE just created.

        backend="uia" talks to apps through UI Automation, the framework
        that also powers screen readers - it understands modern
        Windows/UWP apps (Calculator, Settings, Store apps). The older
        backend="win32" only sees classic win32 controls and simply
        won't find these at all, so uia is the safer default here.
        """
        # TRAP 1: which window is OURS? Searching by title alone breaks the
        # moment one is already open - pywinauto raises
        # ElementAmbiguousError ("there are 12 elements that match") - and
        # picking one at random risks driving, then killing, a window the
        # user opened themselves. So note which ones exist BEFORE we
        # launch and afterwards accept only a handle that is new.
        handles_before = {e.handle for e in self._matching_elements()}

        # TRAP 2: the process we start is often NOT the one that ends up
        # owning the window. Several modern apps (Calculator included)
        # launch via a short-lived stub that hands off to the real app
        # under a different process id - launching calc.exe really runs
        # CalculatorApp.exe. So we ignore the object start() returns and
        # find the window on its own terms.
        Application(backend="uia").start(self.app_path)

        def usable_window():
            for info in self._matching_elements():
                if info.handle in handles_before:
                    continue

                # Remember the app as soon as our window appears, so
                # close() can still kill it if the UI never finishes
                # loading. Without this, every failed open() leaks a
                # window - and a pile of them makes the title ambiguous
                # for every later run (see TRAP 1).
                self.app = Application(backend="uia").connect(
                    process=info.process_id
                )
                spec = self.app.window(handle=info.handle)

                # TRAP 3: a window is not the same thing as a loaded UI. A
                # modern app's visible window is only an outer shell (its
                # class name is literally ApplicationFrameWindow) and the
                # real interface lives in a separate window created inside
                # it. Until that exists, asking for a button raises
                # ElementNotFoundError naming the frame as the parent.
                # Accepting only a window that already contains a known
                # control skips both the frame and the loading gap.
                if self.ready_control and not spec.child_window(
                    **self.ready_control
                ).exists():
                    raise LookupError("window is up but its UI is not loaded yet")
                return spec
            raise LookupError(f"no new {self.window_title!r} window yet")

        try:
            self.window = wait_until_passes(
                WAIT_TIMEOUT, RETRY_INTERVAL, usable_window, exceptions=(LookupError,)
            )
        except WaitTimeoutError:
            # pywinauto would raise a bare "timed out" here, which tells
            # you nothing. Explain the usual cause instead.
            raise RuntimeError(
                f"{self.window_title!r} never became usable within "
                f"{WAIT_TIMEOUT}s.\n"
                "Its window appeared but the UI inside it never loaded. The "
                "usual cause is that the desktop is not free: another window "
                "is covering the app or holding the foreground, the screen is "
                "locked, or this is a remote session. Desktop UI automation "
                "drives real windows, so it needs a real, visible, unlocked "
                "desktop - it cannot run headless."
            ) from None

        self.window.wait("visible ready", timeout=WAIT_TIMEOUT)

        # Bring the window to the front. Some interactions (typing, and
        # click_input()'s real mouse clicks) go wherever the foreground
        # window is, so a background window means input lands elsewhere.
        # Note Windows may refuse this while another app holds the
        # foreground - one more reason to use .click() over click_input().
        self.window.set_focus()
        return self

    def close(self):
        """
        Force-close the app and everything it spawned. The `calculator`
        fixture calls this in teardown so apps never pile up between runs,
        the same way delete_account() cleans up accounts on the web side.

        Safe to call even when open() failed part-way, which is exactly
        when it matters most - see the fixture's try/finally.
        """
        if self.app is not None:
            self.app.kill()
            self.app = None
            self.window = None
