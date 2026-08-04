/* One zone: the lesson, with its challenges alongside as a rail.
 *
 * Read a little, then do a lot. The lesson is short on purpose - it is
 * a condensation of the guide (docs/qa-automation-guide.html), which
 * stays the source of truth for the long version.
 *
 * The layout is a rail plus a reading column rather than one wide page,
 * for two reasons: prose wants a measure of about 65 characters and the
 * page is 1240px, so something has to fill the rest; and a learner
 * halfway through a zone needs to see what is left without scrolling
 * past the lesson they have already read.
 */

import { h } from "../dom.js";
import { Game } from "../game.js";
import { Store } from "../store.js";

var KIND_LABELS = {
  "write-the-test": "Write the test",
  "fill-the-blank": "Fill the blank",
  "fix-the-broken-test": "Fix the broken test",
  "spot-the-flake": "Spot the flake",
  "refactor-to-pom": "Refactor to page objects",
  "predict-the-error": "Predict the error",
  "read-the-trace": "Read the trace",
  "locator-match": "Locator practice",
  "quiz": "Quiz"
};

// --------------------------------------------------------------- the rail

function railItem(zone, challenge, index) {
  var record = Store.record(zone.id, challenge.id);
  var passed = record.status === "passed";
  // The first unfinished one is where a returning learner belongs.
  var current = !passed && zone.challenges.slice(0, index).every(function (earlier) {
    return Store.isPassed(zone.id, earlier.id);
  });

  var state = h("span", {
    class: "rail-mark" + (passed ? " done" : "") + (current ? " now" : ""),
    "aria-hidden": "true",
    text: passed ? "✓" : ""
  });

  return h("li", { class: "challenge-row" + (passed ? " passed" : "") }, [
    h("a", {
      class: "challenge-link" + (current ? " current" : ""),
      href: "#/zone/" + zone.id + "/" + challenge.id,
      "aria-current": current ? "step" : null
    }, [
      state,
      h("span", { class: "rail-index", text: String(index + 1) }),
      h("span", { class: "challenge-title", text: challenge.title }),
      challenge.boss ? h("span", { class: "tag tag-boss", text: "Boss" }) : null
    ]),
    passed ? h("span", { class: "sr-only", text: "cleared" }) : null
  ]);
}

function rail(zone) {
  var cards = [];

  if (zone.challenges.length) {
    cards.push(h("nav", { class: "rail-card", "aria-label": "Challenges in this zone" }, [
      h("p", { class: "panel-kind", text: zone.title }),
      h("ol", { class: "rail-list" }, zone.challenges.map(function (challenge, index) {
        return railItem(zone, challenge, index);
      }))
    ]));
  } else {
    cards.push(h("div", { class: "rail-card" }, [
      h("p", { class: "panel-kind", text: "Planned" }),
      h("ol", { class: "rail-list stub" }, (zone.plannedChallenges || []).map(function (title) {
        return h("li", { class: "planned", text: title });
      }))
    ]));
  }

  // Where this material lives in the kit itself. The site is a
  // re-presentation; these are the originals, and a learner who wants
  // the long version should be one click from it.
  if (zone.source && zone.source.length) {
    cards.push(h("div", { class: "rail-card" }, [
      h("p", { class: "panel-kind", text: "Keep nearby" }),
      h("ul", { class: "source-list" }, zone.source.map(function (item) {
        return h("li", { text: item });
      })),
      h("p", { class: "small muted",
        text: "Everything on this page is in there, in more detail and less English." })
    ]));
  }

  return h("aside", { class: "zone-rail" }, cards);
}

// --------------------------------------------------------- the main column

function subtitle(zone) {
  var progress = Game.zoneProgress(zone.id);
  var bits = [];
  if (zone.teaches) bits.push(zone.teaches);
  if (progress.total) {
    bits.push(progress.passed + " of " + progress.total + " cleared");
  } else {
    bits.push("mapped, not built yet");
  }
  return bits.join(" · ");
}

/** The one button that answers "so what do I do?". */
function callToAction(zone) {
  var next = zone.challenges.filter(function (challenge) {
    return !Store.isPassed(zone.id, challenge.id);
  })[0];
  if (!next) {
    if (!zone.challenges.length) return null;
    return h("p", { class: "zone-cta" }, [
      h("a", { class: "btn primary", href: "#/cleared/" + zone.id,
               text: "See what you earned" })
    ]);
  }
  var started = zone.challenges.some(function (challenge) {
    return Store.isPassed(zone.id, challenge.id);
  });
  return h("p", { class: "zone-cta" }, [
    h("a", {
      class: "btn primary",
      href: "#/zone/" + zone.id + "/" + next.id,
      text: (started ? "Continue · " : "Start · ") + next.title
    }),
    h("span", { class: "small muted",
      text: " " + (KIND_LABELS[next.kind] || next.kind) + " · " + next.xp + " XP" })
  ]);
}

export function renderZone(content, zoneId) {
  var zone = content.zones.filter(function (z) { return z.id === zoneId; })[0];
  if (!zone) return h("p", { text: "No such zone." });

  var head = h("header", { class: "zone-head" }, [
    h("p", { class: "crumb" }, [
      h("a", { href: "#/", text: "Map" }),
      h("span", { text: " / " }),
      h("span", { text: zone.title })
    ]),
    h("h1", { text: zone.title }),
    h("p", { class: "zone-sub", text: subtitle(zone) })
  ]);

  var objectives = (zone.objectives || []).length
    ? h("section", { class: "objectives" }, [
        h("p", { class: "panel-kind", text: "By the end of this zone you can" }),
        h("ul", {}, zone.objectives.map(function (item) {
          return h("li", { text: item });
        }))
      ])
    : null;

  var lesson = h("section", { class: "lesson", html: zone.lesson || "" });

  var stub = zone.challenges.length
    ? null
    : h("p", { class: "note small muted",
        text: "This zone is mapped out but not built yet. "
          + "site/CONTRIBUTING-CONTENT.md explains how to add a challenge - "
          + "it is a single JSON file, no engine code." });

  var main = h("article", { class: "zone-main" },
    [head, objectives, lesson, stub, callToAction(zone)]);

  return h("div", { class: "view view-zone" }, [
    h("div", { class: "zone-layout" }, [rail(zone), main])
  ]);
}
