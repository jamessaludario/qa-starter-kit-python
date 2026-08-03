"""Everything the shim needs that is not part of Playwright's own API.

Two jobs:

1. Hold the bridge - the object that actually touches the DOM. In the
   browser it is a JavaScript module registered by Pyodide; in the unit
   tests it is a plain Python fake. The shim itself never knows which,
   which is exactly why it can be tested without a browser.

2. Record an action log. Challenges are graded on BEHAVIOUR - what the
   learner's code did to the app - not on what their source looks like,
   so we need an honest record of every call that reached the page.
"""

BRIDGE = None

# One entry per action or assertion the learner's code performed.
ACTION_LOG = []


def bind(bridge):
    """Install the object that talks to the DOM (called once at boot)."""
    global BRIDGE
    BRIDGE = bridge


def reset_log():
    """Start a fresh recording. Called before every challenge run."""
    del ACTION_LOG[:]


def record(method, target, chain, args=None, ok=True, detail=""):
    """Remember one thing the learner's code did."""
    ACTION_LOG.append({
        "method": method,
        "target": target,
        # Which KINDS of locator were used ("role", "css", "text", ...).
        # This is what lets a challenge insist on a role-based locator
        # without ever string-matching the learner's source code.
        "kinds": [step["k"] for step in chain],
        # The chain itself, so the site can re-resolve it afterwards and
        # highlight what the learner's locator actually matched.
        "chain": list(chain),
        "args": list(args or []),
        "ok": ok,
        "detail": detail,
        "at": BRIDGE.now() if BRIDGE is not None else 0,
    })
