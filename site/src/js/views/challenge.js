/* One challenge: brief, editor, the shop, and an honest verdict.
 *
 * The feedback order is the order a reviewer would use, and it never
 * skips a step:
 *
 *   syntax error  -> the line, in plain words
 *   review note   -> what a senior colleague would say, and why
 *   crash         -> Playwright's own error message, unedited
 *   failed check  -> what the shop looked like versus what was asked
 *
 * A red X on its own teaches nothing, so there is never a red X on its own.
 */

import { announce, clear, h } from "../dom.js";
import { createEditor } from "../editor.js";
import { Game } from "../game.js";
import { grade, roleLocatorCount } from "../grade.js";
import { Runner } from "../runner.js";
import { Store } from "../store.js";

var DRAFT_PREFIX = "quest-draft.";

function draftKey(zoneId, challengeId) {
  return DRAFT_PREFIX + zoneId + "/" + challengeId;
}

function loadDraft(zoneId, challengeId) {
  try {
    return window.localStorage.getItem(draftKey(zoneId, challengeId));
  } catch (error) { return null; }
}

function saveDraft(zoneId, challengeId, text) {
  try {
    window.localStorage.setItem(draftKey(zoneId, challengeId), text);
  } catch (error) { /* storage off - the editor still works */ }
}

// --------------------------------------------------------------- feedback

function findingCard(finding) {
  return h("div", { class: "finding " + finding.severity }, [
    h("p", { class: "finding-head" }, [
      h("span", { class: "finding-badge",
                  text: finding.severity === "error" ? "Change requested" : "Suggestion" }),
      h("strong", { text: finding.title }),
      h("span", { class: "finding-line", text: "line " + finding.line })
    ]),
    h("p", { class: "finding-body", text: finding.message })
  ]);
}

function checkRow(check) {
  return h("li", { class: "check " + (check.ok ? "ok" : "bad") }, [
    h("span", { class: "check-mark", "aria-hidden": "true", text: check.ok ? "✓" : "✗" }),
    h("span", {}, [
      h("span", { class: "check-label", text: check.label }),
      check.feedback ? h("span", { class: "check-feedback", text: check.feedback }) : null
    ])
  ]);
}

// ---------------------------------------------------------------- the view

export function renderChallenge(content, zoneId, challengeId, navigate) {
  var zone = content.zones.filter(function (z) { return z.id === zoneId; })[0];
  if (!zone) return h("p", { text: "No such zone." });
  var challenge = zone.challenges.filter(function (c) { return c.id === challengeId; })[0];
  if (!challenge) return h("p", { text: "No such challenge." });

  var record = Store.record(zoneId, challengeId);
  var results = h("div", { class: "results", role: "status", "aria-live": "polite" }, [
    // An empty panel looks broken. Say what it is waiting for.
    h("p", { class: "small muted results-idle",
      text: "Nothing has run yet. Write your test, hit Run, and this is where "
        + "the review, the failure and the checks appear." })
  ]);
  var startedAt = Date.now();

  // --- the shop under test -------------------------------------------
  var iframe = h("iframe", {
    class: "app-frame",
    title: "AutomationVille - the practice shop your test drives",
    src: "mockapp/index.html",
    // allow-same-origin is required: the synchronous bridge reads
    // contentDocument directly. The sandbox still blocks top-level
    // navigation, popups and modal dialogs, so learner code stays inside
    // this box.
    sandbox: "allow-scripts allow-same-origin allow-forms"
  });
  var appReady = new Promise(function (resolve) {
    iframe.addEventListener("load", function () {
      Runner.useIframe(function () { return iframe; });
      Runner.bridge.reset_app(JSON.stringify(challenge.scenario || {}));
      resolve();
    });
  });

  // --- work area ------------------------------------------------------
  var work;
  var getSources;

  if (challenge.kind === "quiz" || challenge.kind === "predict-the-error"
      || challenge.kind === "read-the-trace") {
    work = quizArea(challenge, function (passed, detail) {
      finish(passed, detail, { clean: true, sleepFlagged: false });
    });
  } else if (challenge.kind === "locator-match") {
    var inspector = inspectorArea(challenge, run);
    work = inspector.element;
    getSources = inspector.getSources;
  } else {
    var editorArea = codeArea(zoneId, challenge, record, run);
    work = editorArea.element;
    getSources = editorArea.getSources;
    var editor = editorArea.editor;
  }

  // --- hints -----------------------------------------------------------
  var hintsBox = hintPanel(challenge, record);

  // --- running ---------------------------------------------------------

  function setBusy(busy) {
    var button = results.parentNode && results.parentNode.querySelector(".run-btn");
    if (button) {
      button.disabled = busy;
      button.textContent = busy ? "Running..." : "Run test";
    }
  }

  async function run() {
    clear(results);
    results.appendChild(h("p", { class: "muted", text: "Booting Python..." }));
    setBusy(true);
    try {
      await appReady;
      await Runner.boot(reportBoot);
    } catch (error) {
      clear(results);
      results.appendChild(h("pre", { class: "crash", text: String(error.message || error) }));
      setBusy(false);
      return;
    }
    clear(results);
    var outcome;
    try {
      outcome = Runner.run(challenge, getSources());
    } catch (error) {
      results.appendChild(h("pre", { class: "crash",
        text: "The Python runtime itself failed:\n" + (error.message || error) }));
      setBusy(false);
      return;
    }
    setBusy(false);
    var verdict = grade(challenge, outcome, Runner);
    if (challenge.kind === "locator-match") highlightLast(outcome);
    showVerdict(outcome, verdict);
    finish(verdict.passed, null, verdict, outcome);
  }

  function reportBoot(progress) {
    clear(results);
    if (progress.phase === "download" && progress.total) {
      var mb = (progress.loaded / 1048576).toFixed(1);
      var totalMb = (progress.total / 1048576).toFixed(1);
      results.appendChild(h("p", { class: "muted",
        text: "Downloading the Python runtime: " + mb + " MB of " + totalMb + " MB" }));
      results.appendChild(h("div", { class: "bar" }, [
        h("div", { class: "bar-fill", style: "width:" + (progress.loaded / progress.total * 100) + "%" })
      ]));
      results.appendChild(h("p", { class: "muted small",
        text: "One time only - it is cached afterwards, and the site works offline from then on." }));
    } else {
      results.appendChild(h("p", { class: "muted", text: progress.note + "..." }));
    }
  }

  function highlightLast(outcome) {
    var withChain = (outcome.log || []).filter(function (entry) {
      return entry.chain && entry.chain.length;
    });
    if (withChain.length) Runner.bridge.highlight(JSON.stringify(withChain[withChain.length - 1].chain));
  }

  // --- verdict rendering -----------------------------------------------

  function showVerdict(outcome, verdict) {
    clear(results);

    if (outcome.syntax) {
      var syntax = outcome.syntax;
      results.appendChild(h("div", { class: "verdict bad" }, [
        h("h3", { text: "Python could not read line " + syntax.line }),
        h("p", { text: syntax.message + "." }),
        syntax.text ? h("pre", { class: "crash", text: syntax.text }) : null,
        h("p", { class: "small muted",
                 text: "Usually a missing bracket or quote, or a colon at the end "
                   + "of a def/if/for line." })
      ]));
      if (editor) editor.markLine(syntax.line);
      return;
    }

    if (verdict.findings.length) {
      results.appendChild(h("div", { class: "review" }, [
        h("h3", { text: verdict.stage === "rubric"
          ? "Code review: not yet" : "Code review: notes" }),
        h("p", { class: "small muted", text: verdict.stage === "rubric"
          ? "I stopped before running this - a reviewer would have too."
          : "It passed, and here is what I would still change." })
      ].concat(verdict.findings.map(findingCard))));
      if (verdict.stage === "rubric") {
        if (editor) editor.markLine(verdict.findings[0].line);
        return;
      }
    }

    if (outcome.error) {
      results.appendChild(h("div", { class: "verdict bad" }, [
        h("h3", { text: "Your test ran, and it failed" }),
        h("p", { class: "small muted",
                 text: "This is exactly what you would see in a terminal. Read it "
                   + "top to bottom: what was expected, what was actually there, "
                   + "and what it was waiting for." }),
        h("pre", { class: "crash", text: outcome.error })
      ]));
      if (editor && outcome.errorLine) editor.markLine(outcome.errorLine);
    }

    if (outcome.stdout) {
      results.appendChild(h("details", { class: "stdout" }, [
        h("summary", { text: "Printed output" }),
        h("pre", { text: outcome.stdout })
      ]));
    }

    if (verdict.checks.length) {
      results.appendChild(h("div", { class: "checks" }, [
        h("h3", { text: verdict.passed ? "What I checked" : "What I checked" }),
        h("ul", {}, verdict.checks.map(checkRow))
      ]));
    }

    if (outcome.virtualMs) {
      results.appendChild(h("p", { class: "small muted",
        text: "Page time used: " + outcome.virtualMs + " ms. "
          + "That is how long the shop took to respond while your test waited "
          + "for it - and expect() waited exactly that long, no more." }));
    }
  }

  // --- scoring ---------------------------------------------------------

  function finish(passed, detail, verdict, outcome) {
    record.attempts += 1;
    record.sleepFlagged = record.sleepFlagged || !!(verdict && verdict.sleepFlagged);
    Store.data.stats.runs += 1;
    if (outcome) {
      Store.data.stats.roleLocators += roleLocatorCount(outcome);
      record.virtualMs = outcome.virtualMs || 0;
    }
    if (verdict && verdict.sleepFlagged) Store.data.stats.sleepAttempts += 1;

    if (!passed) { Store.save(); return; }

    var alreadyPassed = record.status === "passed";
    record.status = "passed";
    var award = null;
    if (!alreadyPassed) {
      award = Game.scoreFor(challenge, record, { passed: true, clean: !!(verdict && verdict.clean) });
      record.xp = award.total;
      record.clean = !!(verdict && verdict.clean);
      record.seconds = Math.round((Date.now() - startedAt) / 1000);
      Store.data.xp += award.total;
      if (verdict && verdict.clean) Store.data.stats.cleanRuns += 1;
    }
    var newBadges = Game.refreshBadges();
    Store.save();
    results.appendChild(successCard(zone, challenge, award, newBadges, detail, navigate));
    announce("Challenge cleared" + (award ? ", " + award.total + " XP earned" : ""));
  }

  // --- assembly ---------------------------------------------------------

  var isQuiz = challenge.kind === "quiz" || challenge.kind === "predict-the-error"
    || challenge.kind === "read-the-trace";

  var runButton = h("button", { class: "btn primary run-btn", type: "button", onclick: run },
                    ["Run test"]);
  var resetButton = h("button", {
    class: "btn ghost small", type: "button",
    onclick: function () {
      if (Runner.bridge) Runner.bridge.reset_app(JSON.stringify(challenge.scenario || {}));
      announce("Shop reset");
    }
  }, ["Reset the shop"]);

  var topBar = h("div", { class: "challenge-bar" }, [
    h("p", { class: "crumb" }, [
      h("a", { href: "#/", text: "Map" }),
      h("span", { text: " / " }),
      h("a", { href: "#/zone/" + zoneId, text: zone.title }),
      h("span", { text: " / " }),
      h("span", { text: challenge.title })
    ]),
    isQuiz ? null : h("div", { class: "bar-actions" }, [resetButton, runButton])
  ]);

  // Left rail: what to do, help if you want it, and what it pays.
  var rail = h("aside", { class: "challenge-rail" }, [
    objectivePanel(challenge, record),
    hintsBox,
    scoringPanel(challenge, record)
  ]);

  var centre = h("div", { class: "challenge-work" }, [
    h("div", { class: "brief", html: challenge.brief || "" }),
    work,
    isQuiz ? null : h("p", { class: "small muted run-hint",
      text: "Ctrl+Enter runs. Esc then Tab leaves the editor." })
  ]);

  // Right rail: the app under test, then whatever the last run said.
  var side = h("aside", { class: "challenge-side" }, [
    h("div", { class: "browser-frame" }, [
      h("div", { class: "browser-chrome" }, [
        h("span", { class: "browser-dots", "aria-hidden": "true" }),
        h("span", { class: "browser-url", text: "automationville.test" }),
        h("span", { class: "browser-badge", text: "MOCK" })
      ]),
      iframe
    ]),
    h("p", { class: "small muted",
             text: "A stand-in for automationexercise.com with the same ids and "
               + "class names, so your locators transfer straight to the real site." }),
    h("div", { class: "results-panel" }, [
      h("p", { class: "panel-kind", text: "Results" }),
      results
    ])
  ]);

  return h("div", { class: "view view-challenge" }, [
    topBar,
    h("div", { class: "challenge-layout" }, [rail, centre, side])
  ]);
}

// ----------------------------------------------------------------- panels

/**
 * What the challenge is asking for, as a checklist.
 *
 * Built from the same `checks` the grader runs, so it can never drift
 * from what is actually marked - a brief that promises one thing while
 * the grader wants another is the worst bug this site could have.
 */
function objectivePanel(challenge, record) {
  var checks = (challenge.checks || []).filter(function (check) { return check.label; });
  return h("section", { class: "rail-card objective" }, [
    h("p", { class: "panel-kind", text: "Objective" }),
    h("p", { class: "objective-title", text: challenge.title }),
    checks.length
      ? h("ul", { class: "objective-list" }, checks.map(function (check) {
          return h("li", {}, [
            h("span", { class: "objective-box", "aria-hidden": "true" }),
            h("span", { text: check.label })
          ]);
        }))
      : null,
    record.status === "passed"
      ? h("p", { class: "objective-done", text: "Cleared - " + record.xp + " XP banked." })
      : null
  ]);
}

/** What this attempt can pay, and what would cost you. */
function scoringPanel(challenge, record) {
  var base = challenge.xp || 20;
  var rules = Game.content.game.xp;
  var spent = (record.hints || []).reduce(function (sum, hint) {
    return sum + (hint.cost || 0);
  }, 0);

  function line(label, value, muted) {
    return h("li", { class: muted ? "muted" : "" }, [
      h("span", { text: label }),
      h("strong", { text: value })
    ]);
  }

  return h("section", { class: "rail-card scoring" }, [
    h("p", { class: "panel-kind", text: "Scoring" }),
    h("ul", { class: "scoring-list" }, [
      line("Challenge passed", "+" + base),
      line("First try", "+" + Math.round(base * rules.firstTryBonus),
           record.attempts > 0),
      line("Clean review", "+" + Math.round(base * rules.cleanBonus)),
      spent ? line("Hints spent", "-" + spent) : null
    ]),
    h("p", { class: "small muted",
      text: "Clean means no advisory findings: a role or label locator where one "
        + "fits, no time.sleep(), no XPath. Hints never take you below "
        + Math.round(base * rules.hintFloor) + " XP." })
  ]);
}

// ------------------------------------------------------------- work areas

/** One file: a name tab, the editor, and optionally a status strip. */
function editorCard(name, editor, status) {
  return h("div", { class: "editor-card" }, [
    h("div", { class: "editor-tabs" }, [
      h("span", { class: "editor-tab active", text: name })
    ]),
    editor.element,
    status
  ]);
}

/**
 * The strip under the editor.
 *
 * Says what is ACTUALLY running. The temptation is to write "pytest 8.2
 * - chromium" because it looks the part, but this is CPython compiled to
 * WebAssembly driving a mock DOM through a shim, and a teaching site
 * that misstates its own runtime has no business grading anybody's
 * honesty about theirs.
 */
function statusBar() {
  return h("div", { class: "editor-status" }, [
    h("span", { text: "python · pyodide" }),
    h("span", { text: "playwright_lite" }),
    h("span", { text: "UTF-8" }),
    h("span", { class: "status-run", text: "Ctrl+Enter to run" })
  ]);
}

function codeArea(zoneId, challenge, record, run) {
  var draft = loadDraft(zoneId, challenge.id);
  var editor = createEditor({
    label: "Your test code",
    onRun: run,
    onChange: function (text) { saveDraft(zoneId, challenge.id, text); }
  });
  editor.value = draft === null ? (challenge.starter || "") : draft;

  var cells = (challenge.cells || []).map(function (cell) {
    var cellEditor = createEditor({ label: cell.label || cell.name, onRun: run,
      onChange: function (text) { saveDraft(zoneId, challenge.id + ":" + cell.name, text); } });
    var saved = loadDraft(zoneId, challenge.id + ":" + cell.name);
    cellEditor.value = saved === null ? (cell.starter || "") : saved;
    return { spec: cell, editor: cellEditor };
  });

  var element = h("div", { class: "work" },
    cells.map(function (cell) {
      return editorCard(cell.spec.name, cell.editor, null);
    }).concat([
      editorCard("test_challenge.py", editor, statusBar()),
      h("p", { class: "reset-code" }, [
        h("button", {
          class: "linky", type: "button",
          onclick: function () { editor.value = challenge.starter || ""; editor.focus(); }
        }, ["Restore the starting code"])
      ])
    ]));

  // Paint once the editor is in the document, so line heights are real.
  window.requestAnimationFrame(function () {
    editor.refresh();
    cells.forEach(function (cell) { cell.editor.refresh(); });
  });

  return {
    element: element,
    editor: editor,
    getSources: function () {
      return {
        main: editor.value,
        cells: cells.map(function (cell) {
          return {
            name: cell.spec.name,
            label: cell.spec.label,
            source: cell.editor.value,
            rubric: cell.spec.rubric || []
          };
        })
      };
    }
  };
}

function inspectorArea(challenge, run) {
  var input = h("input", {
    class: "locator-input", type: "text", spellcheck: "false",
    "aria-label": "Locator expression, written after page.",
    placeholder: challenge.placeholder || 'get_by_role("link", name="Cart")'
  });
  input.value = challenge.starter || "";
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") { event.preventDefault(); run(); }
  });

  var element = h("div", { class: "work inspector" }, [
    h("label", { class: "inspector-line" }, [
      h("span", { class: "inspector-prefix", text: "page." }),
      input
    ]),
    h("p", { class: "small muted",
             text: "Whatever you write is put inside a real test that asserts how "
               + "many elements it matches. Matches get outlined in the shop." })
  ]);

  return {
    element: element,
    getSources: function () {
      var body = (challenge.template || DEFAULT_INSPECTOR_TEMPLATE)
        .replace("{{expr}}", input.value.trim() || "locator('nothing-typed-yet')")
        .replace("{{count}}", String(challenge.expectCount));
      return { main: body, cells: [] };
    }
  };
}

var DEFAULT_INSPECTOR_TEMPLATE = [
  "from playwright.sync_api import Page, expect",
  "",
  "",
  "def test_locator_points_at_the_right_thing(page: Page):",
  "    target = page.{{expr}}",
  "    expect(target).to_have_count({{count}})",
  ""
].join("\n");

function quizArea(challenge, onDone) {
  var form = h("form", { class: "work quiz" });
  var state = challenge.questions.map(function () { return null; });

  challenge.questions.forEach(function (question, qi) {
    var options = question.options.map(function (option, oi) {
      var id = "q" + qi + "o" + oi;
      var radio = h("input", { type: "radio", name: "q" + qi, id: id, value: String(oi) });
      radio.addEventListener("change", function () { state[qi] = oi; });
      return h("li", {}, [radio, h("label", { for: id, text: option })]);
    });
    form.appendChild(h("fieldset", { class: "question" }, [
      h("legend", { text: "Question " + (qi + 1) }),
      h("div", { class: "question-prompt", html: question.prompt }),
      question.code ? h("pre", { class: "sample" }, [h("code", { text: question.code })]) : null,
      h("ul", { class: "options" }, options)
    ]));
  });

  var feedback = h("div", { class: "quiz-feedback" });
  form.appendChild(h("div", { class: "toolbar" }, [
    h("button", { class: "btn primary", type: "submit" }, ["Check my answers"])
  ]));
  form.appendChild(feedback);

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    clear(feedback);
    var correct = 0;
    challenge.questions.forEach(function (question, qi) {
      var ok = state[qi] === question.answer;
      if (ok) correct += 1;
      feedback.appendChild(h("div", { class: "finding " + (ok ? "advice" : "error") }, [
        h("p", { class: "finding-head" }, [
          h("span", { class: "finding-badge", text: ok ? "Right" : "Not quite" }),
          h("strong", { text: "Question " + (qi + 1) })
        ]),
        h("p", { class: "finding-body", text: question.why })
      ]));
    });
    var passed = correct === challenge.questions.length;
    onDone(passed, correct + " of " + challenge.questions.length + " correct");
  });

  return form;
}

function hintPanel(challenge, record) {
  var hints = challenge.hints || [];
  if (!hints.length) return h("div");
  var spent = (record.hints || []).length;
  var box = h("section", { class: "rail-card hints" });
  box.appendChild(h("p", { class: "panel-kind" }, [
    h("span", { text: "Hints" }),
    h("span", { class: "hints-spent",
      text: spent ? spent + " of " + hints.length + " spent" : "none spent" })
  ]));
  box.appendChild(h("p", { class: "small muted",
    text: "Each hint costs a little XP - not as a punishment, but because "
      + "the struggle before the hint is where the learning happens." }));

  hints.forEach(function (hint, index) {
    var used = (record.hints || []).some(function (h2) { return h2.index === index; });
    var body = h("p", { class: "hint-body", text: hint.text, hidden: !used });
    var button = h("button", {
      class: "btn ghost small", type: "button", hidden: used,
      onclick: function () {
        record.hints = record.hints || [];
        record.hints.push({ index: index, cost: hint.cost });
        Store.save();
        body.hidden = false;
        button.hidden = true;
        announce("Hint revealed");
      }
    }, [(hint.label || "Hint " + (index + 1)) + " (-" + hint.cost + " XP)"]);
    box.appendChild(h("div", { class: "hint" }, [button, body]));
  });
  return box;
}

function successCard(zone, challenge, award, badges, detail, navigate) {
  var index = zone.challenges.indexOf(challenge);
  var next = zone.challenges[index + 1];
  var lines = award
    ? award.reasons.map(function (reason) {
        return h("li", {}, [
          h("span", { text: reason.label }),
          h("strong", { text: (reason.xp >= 0 ? "+" : "") + reason.xp + " XP" })
        ]);
      })
    : [h("li", {}, [h("span", { text: "Already cleared - no XP twice" })])];

  return h("div", { class: "verdict good" }, [
    h("h3", { text: "Cleared" + (detail ? " - " + detail : "") }),
    h("ul", { class: "xp-lines" }, lines),
    award ? h("p", { class: "xp-total", text: "+" + award.total + " XP" }) : null,
    badges.length ? h("p", { class: "badge-earned",
      text: "New badge: " + badges.map(function (b) { return b.name; }).join(", ") }) : null,
    challenge.reveal ? h("div", { class: "reveal", html: challenge.reveal }) : null,
    h("p", { class: "next-up" }, [
      next
        ? h("a", { class: "btn primary", href: "#/zone/" + zone.id + "/" + next.id },
            ["Next: " + next.title])
        : h("a", { class: "btn primary", href: "#/", onclick: function () { navigate("/"); } },
            ["Back to the quest map"])
    ])
  ]);
}
