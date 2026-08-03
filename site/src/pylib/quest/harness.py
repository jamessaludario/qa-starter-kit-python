"""quest/harness.py - runs one attempt at a challenge, the way pytest would.

The order matters and is the same order a good reviewer works in:

    1. Does it parse?            -> a SyntaxError, with the line number
    2. Would a reviewer approve? -> the AST rubric (see rubric.py)
    3. Does it actually work?    -> execute it against the practice shop

Step 2 comes before step 3 on purpose. Code with a `time.sleep()` in it
is not run at all: a sleep would block the whole browser tab for real
seconds, and more importantly a senior reviewer stops at the sleep too.

Everything crosses into JavaScript as JSON, so nothing here depends on
Pyodide's object proxies.
"""

import io
import json
import os
import sys
import time
import traceback

from playwright_lite import _runtime
from playwright_lite.sync_api import Page

from quest import rubric

LEARNER_FILE = "test_challenge.py"
LEARNER_DIR = "/learner"


def install_guards():
    """Disable the things that would freeze the tab. Called once at boot."""
    def blocked_sleep(seconds):
        raise RuntimeError(
            "time.sleep() is switched off on the quest site.\n"
            "That is not censorship - it is the lesson. A sleep would stop "
            "this page for " + str(seconds) + " real seconds and STILL not "
            "wait for the thing you care about. Use expect(...), which "
            "retries until the page is ready."
        )

    time.sleep = blocked_sleep

    os.makedirs(LEARNER_DIR, exist_ok=True)
    if LEARNER_DIR not in sys.path:
        sys.path.insert(0, LEARNER_DIR)


def _syntax_report(error, cell):
    """A SyntaxError, explained without the CPython jargon."""
    return {
        "cell": cell,
        "line": error.lineno or 0,
        "offset": error.offset or 0,
        "message": error.msg,
        "text": (error.text or "").rstrip("\n"),
    }


def _learner_traceback(exc):
    """Show the learner's own frames, not ours."""
    trace = traceback.TracebackException.from_exception(exc)
    ours = [
        frame for frame in trace.stack
        if frame.filename == LEARNER_FILE or frame.filename.startswith(LEARNER_DIR)
    ]
    if ours:
        trace.stack = traceback.StackSummary.from_list(ours)
    line = ours[-1].lineno if ours else 0
    return "".join(trace.format()), line


def _write_cells(cells):
    """Put the learner's extra files (page objects, conftest) on sys.path."""
    written = []
    for cell in cells:
        name = cell.get("name")
        if not name:
            continue
        path = os.path.join(LEARNER_DIR, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # A package needs an __init__.py to be importable, and the learner
        # should not have to remember that in a browser text box.
        folder = os.path.dirname(path)
        while folder != LEARNER_DIR and folder:
            init = os.path.join(folder, "__init__.py")
            if not os.path.exists(init):
                with open(init, "w", encoding="utf-8") as handle:
                    handle.write("")
            folder = os.path.dirname(folder)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(cell.get("source", ""))
        written.append(name)
    return written


def _forget_learner_modules():
    """Drop last attempt's modules so an edit actually takes effect."""
    for name, module in list(sys.modules.items()):
        origin = getattr(getattr(module, "__spec__", None), "origin", None)
        if origin and str(origin).startswith(LEARNER_DIR):
            del sys.modules[name]


def run(payload_json):
    """Grade and run one attempt. Returns a JSON string (see ARCHITECTURE.md)."""
    payload = json.loads(payload_json)
    source = payload.get("source", "")
    cells = payload.get("cells", [])

    result = {
        "ok": False,
        "phase": "syntax",
        "stdout": "",
        "log": [],
        "findings": [],
        "syntax": None,
        "error": None,
        "errorLine": 0,
        "virtualMs": 0,
    }

    # ---------------------------------------------------------- 1. parse
    pieces = [{"name": LEARNER_FILE, "source": source, "rubric": payload.get("rubric"),
               "label": "your test"}] + cells
    for piece in pieces:
        try:
            compile(piece.get("source", ""), piece.get("name", LEARNER_FILE), "exec")
        except SyntaxError as error:
            result["syntax"] = _syntax_report(error, piece.get("name", LEARNER_FILE))
            result["errorLine"] = error.lineno or 0
            return json.dumps(result)

    # --------------------------------------------------------- 2. rubric
    result["phase"] = "rubric"
    findings = []
    for piece in pieces:
        config = {"cell_label": piece.get("label", piece.get("name"))}
        for finding in rubric.review(piece.get("source", ""), piece.get("rubric"), config):
            finding["cell"] = piece.get("name", LEARNER_FILE)
            findings.append(finding)
    result["findings"] = findings
    if any(f["severity"] == "error" for f in findings):
        result["errorLine"] = next(f["line"] for f in findings if f["severity"] == "error")
        return json.dumps(result)

    # ------------------------------------------------------- 3. execute
    result["phase"] = "run"
    _runtime.reset_log()
    _forget_learner_modules()
    _write_cells(cells)

    page = Page()
    namespace = {"__name__": "learner_test", "__file__": LEARNER_FILE}
    captured = io.StringIO()
    real_stdout = sys.stdout
    sys.stdout = captured
    try:
        exec(compile(source, LEARNER_FILE, "exec"), namespace)  # noqa: S102

        tests = [
            value for name, value in namespace.items()
            if name.startswith("test_") and callable(value)
        ]
        if not tests:
            result["error"] = (
                "No test function found.\n"
                "pytest collects functions whose name starts with test_, so "
                "your code needs to live inside one:\n\n"
                "    def test_something_useful(page):\n        ..."
            )
        else:
            for test in tests:
                # Match pytest: pass the `page` fixture only if asked for.
                if test.__code__.co_argcount:
                    test(page)
                else:
                    test()
            result["ok"] = True
            result["phase"] = "pass"
    except Exception as error:                              # noqa: BLE001
        text, line = _learner_traceback(error)
        result["error"] = text
        result["errorLine"] = line
    finally:
        sys.stdout = real_stdout
        result["stdout"] = captured.getvalue()
        result["log"] = list(_runtime.ACTION_LOG)
        result["virtualMs"] = _runtime.BRIDGE.now() if _runtime.BRIDGE else 0

    return json.dumps(result)
