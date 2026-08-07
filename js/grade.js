/* Grading: did the learner's code DO the right thing?
 *
 * Three independent sources of truth, none of them the learner's source
 * code:
 *
 *   1. the action log      - what their test actually did to the page
 *   2. the app snapshot    - what state the shop ended up in
 *   3. the live DOM        - what is on screen now
 *
 * Plus the AST rubric (rubric.py), which is about HOW it was written.
 * Deliberately never: string-matching the solution. A learner who finds
 * a better locator than ours should pass, and one who pastes our
 * solution with a sleep bolted on should not.
 */

import { get } from "./dom.js";

var COMPARATORS = {
  equals: function (actual, expected) { return actual === expected; },
  notEquals: function (actual, expected) { return actual !== expected; },
  atLeast: function (actual, expected) { return Number(actual) >= expected; },
  atMost: function (actual, expected) { return Number(actual) <= expected; },
  contains: function (actual, expected) {
    if (Array.isArray(actual)) return actual.indexOf(expected) !== -1;
    return String(actual).indexOf(expected) !== -1;
  },
  isTrue: function (actual) { return actual === true; },
  isFalse: function (actual) { return actual === false; }
};

function compare(check, actual) {
  var names = Object.keys(COMPARATORS).filter(function (name) {
    return Object.prototype.hasOwnProperty.call(check, name);
  });
  if (!names.length) return { ok: actual !== undefined && actual !== null, actual: actual };
  var ok = names.every(function (name) {
    return COMPARATORS[name](actual, check[name]);
  });
  return { ok: ok, actual: actual };
}

function matchesAction(entry, check) {
  if (check.method && entry.method !== check.method) return false;
  if (check.targetContains && String(entry.target).indexOf(check.targetContains) === -1) {
    return false;
  }
  if (check.value !== undefined && entry.args.indexOf(check.value) === -1) return false;
  // `locatorKind` here, not `kind` - `kind` already names the check type.
  if (check.locatorKind && entry.kinds.indexOf(check.locatorKind) === -1) return false;
  return true;
}

var EVALUATORS = {
  state: function (check, result) {
    return compare(check, get(result.snapshot, check.path));
  },
  dom: function (check, result, runner) {
    return compare(check, runner.countCss(check.selector));
  },
  action: function (check, result) {
    var hits = result.log.filter(function (entry) {
      return entry.ok !== false && matchesAction(entry, check);
    });
    return compare({ atLeast: check.atLeast === undefined ? 1 : check.atLeast }, hits.length);
  },
  matcher: function (check, result) {
    var wanted = "expect." + check.name;
    var hits = result.log.filter(function (entry) { return entry.method === wanted; });
    return compare({ atLeast: check.atLeast === undefined ? 1 : check.atLeast }, hits.length);
  },
  locatorKind: function (check, result) {
    var hits = result.log.filter(function (entry) {
      return entry.kinds.indexOf(check.name) !== -1;
    });
    return compare({ atLeast: check.atLeast === undefined ? 1 : check.atLeast }, hits.length);
  },
  printed: function (check, result) {
    return compare({ contains: check.contains }, result.stdout);
  },
  virtualMs: function (check, result) {
    return compare(check, result.virtualMs);
  }
};

/** Count role-based locators, for the Selector Sniper badge. */
export function roleLocatorCount(result) {
  return (result.log || []).filter(function (entry) {
    return entry.kinds && entry.kinds.indexOf("role") !== -1;
  }).length;
}

/**
 * Turn a raw run result into a verdict.
 *
 * Returns { passed, stage, checks, findings, clean, sleepFlagged }.
 * `stage` says WHERE it stopped, so the UI can lead with the right
 * thing: a syntax error, a review comment, a crash, or a failed check.
 */
export function grade(challenge, result, runner) {
  var findings = result.findings || [];
  var errors = findings.filter(function (f) { return f.severity === "error"; });
  var verdict = {
    passed: false,
    stage: result.phase,
    checks: [],
    findings: findings,
    clean: findings.length === 0,
    sleepFlagged: findings.some(function (f) { return f.rule === "no-sleep"; })
  };

  if (result.syntax) { verdict.stage = "syntax"; return verdict; }
  if (errors.length) { verdict.stage = "rubric"; return verdict; }
  if (!result.ok) { verdict.stage = "error"; return verdict; }

  verdict.stage = "checks";
  verdict.checks = (challenge.checks || []).map(function (check) {
    var evaluate = EVALUATORS[check.kind];
    if (!evaluate) {
      return { ok: false, label: check.label || check.kind,
               feedback: "Unknown check type: " + check.kind + " (a content bug)." };
    }
    var outcome = evaluate(check, result, runner);
    return {
      ok: outcome.ok,
      label: check.label || describeCheck(check),
      actual: outcome.actual,
      feedback: outcome.ok ? "" : (check.feedback || defaultFeedback(check, outcome.actual))
    };
  });

  verdict.passed = verdict.checks.every(function (check) { return check.ok; });
  return verdict;
}

function describeCheck(check) {
  switch (check.kind) {
    case "state": return "The shop ends up in the right state (" + check.path + ")";
    case "dom": return "The page shows " + check.selector;
    case "action": return "Your test performs " + (check.method || "the action");
    case "matcher": return "You used expect(...)." + check.name + "()";
    case "locatorKind": return "You used a " + check.name + " locator";
    case "printed": return "Your test prints what was asked for";
    case "virtualMs": return "Your test waits for the right amount of time";
    default: return check.kind;
  }
}

function defaultFeedback(check, actual) {
  if (check.kind === "matcher") {
    return "I could not find an expect(...)." + check.name + "() in what your "
      + "test actually ran. Did the line run at all, or is it below a line "
      + "that failed first?";
  }
  if (check.kind === "state" || check.kind === "dom") {
    return "The page did not end up where I expected. I found " +
      JSON.stringify(actual) + ".";
  }
  return "This check did not pass. I found " + JSON.stringify(actual) + ".";
}
