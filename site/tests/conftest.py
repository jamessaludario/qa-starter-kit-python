"""
site/tests/conftest.py
======================
Fixtures for the quest site's OWN test suite.

The site that teaches Playwright is tested with Playwright. That is not
a joke about dogfooding - it is the only honest way to prove the claims
this site makes, because those claims are about what happens in a real
browser: a real DOM, real WebAssembly, real localStorage.

Two things have to exist before a single test can run:

    1. a BUILT site   - dist/ is generated, and git-ignored
    2. an HTTP SERVER - WebAssembly will not load over file://

Both are set up here, once per session.
"""

import socket
import socketserver
import sys
import threading
from functools import partial
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[1]
DIST = SITE / "dist"

# --------------------------------------------------------------------------
# Import paths
# --------------------------------------------------------------------------

# The site's build script, so the suite builds what it is about to test
# instead of trusting whatever happened to be in dist/ from last time.
if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))

# Our page objects live in site/tests/pages/. The REPO ROOT also has a
# pages/ package (the learn track's), and when you run
# `python -m pytest site/tests/` Python puts the repo root on sys.path
# too. Inserting our own folder at position 0 makes sure `from pages...`
# below resolves to the quest site's page objects and not to the other
# ones - a shadowing bug that would otherwise show up as a very
# confusing ImportError.
TESTS = Path(__file__).resolve().parent
if str(TESTS) in sys.path:
    sys.path.remove(str(TESTS))
sys.path.insert(0, str(TESTS))

# Imported here, below the sys.path setup, because that setup is what
# makes it importable at all.
import build_site  # noqa: I001


# --------------------------------------------------------------------------
# Building and serving
# --------------------------------------------------------------------------

# Every path the browser actually asked the SERVER for. The service
# worker tests read this to tell "fetched fresh" from "served out of the
# cache", which is invisible from inside the page.
REQUEST_LOG: list = []


class QuietHandler(build_site.DevHandler):
    """The dev server, plus a request log and no per-request chatter.

    Inherits rather than re-declares: the content types a browser
    insists on and the cache headers that stop a rebuilt site being
    served stale are part of "how this site must be served", and two
    copies of that would drift. The suite would then be testing a
    server the learner never actually uses.
    """

    def do_GET(self):
        REQUEST_LOG.append(self.path)
        super().do_GET()

    def log_message(self, *args):
        """Silence the per-request log: 11 MB of Pyodide is a lot of lines."""


def free_port() -> int:
    """Ask the OS for a port nobody is using.

    A hard-coded port is the classic way to make a suite fail on the one
    machine that already runs something on 8000.
    """
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="session")
def quest_site() -> str:
    """Build the site, serve it, and hand back its base URL.

    Session-scoped: building is fast but serving a fresh server per test
    would be pure overhead, and the server holds no state - every test
    gets its own browser context, which is where the state that matters
    (localStorage) actually lives.
    """
    build_site.build()

    port = free_port()
    # The handler serves the process's working directory unless it is
    # handed one, and the working directory is not ours to assume - so
    # bind dist/ to the class up front, exactly as build_site.py does.
    handler = partial(QuietHandler, directory=str(DIST))
    # Threading, not the plain TCPServer: Pyodide pulls several files at
    # once, and a single-threaded server would serialise them.
    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def server_requests(quest_site: str):
    """Paths the server was asked for, starting empty for each test.

    Cleared rather than snapshotted, because a test wants "what happened
    after this point", not "everything since the session began".
    """
    del quest_site
    REQUEST_LOG.clear()
    return REQUEST_LOG


@pytest.fixture(scope="session")
def base_url(quest_site: str) -> str:
    """Override pytest-playwright's own `base_url`.

    Doing it this way means page objects can call page.goto("/") and
    stay ignorant of which port the OS handed us this run.
    """
    return quest_site


@pytest.fixture(scope="session")
def python_runtime_available(quest_site: str) -> bool:
    """Skip the tests that need Pyodide when it has not been fetched.

    Depends on quest_site so the check happens AFTER the build has had
    its chance to copy the runtime into dist/. Fetching is a deliberate
    one-time 12 MB step, so a fresh clone running this suite should be
    told WHY half of it skipped rather than drown in identical browser
    timeouts.
    """
    del quest_site
    if not (DIST / "vendor" / "pyodide" / "pyodide.js").exists():
        pytest.skip(
            "The Python runtime is not vendored. Run: python site/fetch_vendor.py"
        )
    return True


# --------------------------------------------------------------------------
# Browser configuration
# --------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Every test gets a clean browser, and therefore clean progress.

    pytest-playwright already builds a fresh context per test, which is
    what isolates localStorage. The viewport is pinned so the layout
    assertions mean something: the quest map arranges itself differently
    below 700 px, and a test that passes only on a wide window is a test
    that will surprise somebody.
    """
    return {**browser_context_args, "viewport": {"width": 1280, "height": 900}}


def pytest_report_header(config) -> str:
    """Say up front whether the slow half of the suite can run at all.

    Printed before collection, so "why did 5 tests skip?" is answered
    before it is asked.
    """
    del config
    ready = (SITE / "vendor" / "pyodide" / "pyodide.js").exists()
    return (
        "quest site: pyodide "
        + ("vendored" if ready else "MISSING - run python site/fetch_vendor.py")
    )
