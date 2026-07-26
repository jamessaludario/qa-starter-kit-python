"""
desktop/pages/base_app.py
==========================
The parent class every desktop page object inherits from. It plays the
same role BasePage (pages/base_page.py) plays for the web track: launch
"your" app and hand back its main window, so the child class can get
straight to describing controls.
"""

from pywinauto import Desktop
from pywinauto.application import Application


class BaseApp:
    # Child classes (CalculatorPage, ...) override these with "their"
    # app's launch command and window title, the same way LoginPage
    # overrides BasePage.path.
    app_path = None
    window_title = None

    def __init__(self):
        self.app = None
        self.window = None

    def open(self):
        """
        Launch the app and grab its main window.

        backend="uia" talks to apps through UI Automation, the framework
        that also powers screen readers - it understands modern
        Windows/UWP apps (Calculator, Settings, Store apps). The older
        backend="win32" only sees classic win32 controls and simply
        won't find these at all, so uia is the safer default here.

        Finding the window takes two steps, and both matter.

        STEP 1 - find it by title across the whole desktop. Several
        modern Windows apps (Calculator included) launch via a
        short-lived stub process that immediately hands off to the real
        app under a DIFFERENT process id. Application.start()'s own
        window() lookup filters by the stub's (now-dead) pid, so it waits
        the full timeout and fails even though the window is plainly on
        screen. Desktop(...) isn't tied to a pid, so the handoff can't
        fool it.

        STEP 2 - immediately re-bind to that exact window through its
        OWN process. A Desktop(...) specification re-runs its "any
        top-level window titled X" search on every single use, which is
        both slow and unreliable: it can match a different (or dying)
        window of the same name, and raises ElementNotFoundError outright
        if the window is momentarily unavailable. Binding once to the
        handle we already found gives every later lookup a stable anchor.
        """
        Application(backend="uia").start(self.app_path)

        # Like expect(...) on the web side, this POLLS instead of a
        # fixed sleep: it waits until the window reports itself visible
        # and ready to receive input, up to 10 seconds, then continues
        # the moment it's true (often much sooner).
        found = Desktop(backend="uia").window(title=self.window_title)
        found.wait("visible ready", timeout=10)

        # Resolve the search ONCE into a concrete handle + process id...
        handle = found.handle
        self.app = Application(backend="uia").connect(
            process=found.element_info.process_id
        )
        # ...and from here on talk to that one window, in that one
        # process. Connecting to the real process (not the dead stub)
        # also means close() below can actually kill the app.
        self.window = self.app.window(handle=handle)

        # Bring the window to the front. Some interactions (typing, and
        # click_input()'s real mouse clicks) go wherever the foreground
        # window is, so a background window means input lands in another
        # app entirely.
        self.window.set_focus()
        return self

    def close(self):
        """
        Force-close the app and everything it spawned. Tests call this
        in cleanup (via the `calculator` fixture) so apps never pile up
        between test runs, the same way delete_account() cleans up
        accounts on the web side.
        """
        if self.app is not None:
            self.app.kill()
