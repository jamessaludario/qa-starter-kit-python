/* One zone: the lesson, then its challenges.
 *
 * Read a little, then do a lot. The lesson is short on purpose - it is
 * a condensation of the guide (docs/qa-automation-guide.html), which
 * stays the source of truth for the long version.
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

function challengeRow(zone, challenge, index) {
  var record = Store.record(zone.id, challenge.id);
  var passed = record.status === "passed";
  var kind = KIND_LABELS[challenge.kind] || challenge.kind;

  var tags = [h("span", { class: "tag tag-kind", text: kind })];
  if (challenge.boss) tags.push(h("span", { class: "tag tag-boss", text: "Boss" }));
  tags.push(h("span", { class: "tag tag-xp", text: challenge.xp + " XP" }));

  return h("li", { class: "challenge-row" + (passed ? " passed" : "") }, [
    h("a", { class: "challenge-link", href: "#/zone/" + zone.id + "/" + challenge.id }, [
      h("span", { class: "challenge-status", "aria-hidden": "true",
                  text: passed ? "✓" : String(index + 1) }),
      h("span", { class: "challenge-body" }, [
        h("span", { class: "challenge-title", text: challenge.title }),
        h("span", { class: "challenge-tags" }, tags)
      ])
    ]),
    passed ? h("span", { class: "sr-only", text: "cleared" }) : null
  ]);
}

export function renderZone(content, zoneId) {
  var zone = content.zones.filter(function (z) { return z.id === zoneId; })[0];
  if (!zone) return h("p", { text: "No such zone." });

  var progress = Game.zoneProgress(zone.id);
  var head = h("header", { class: "zone-head" }, [
    h("p", { class: "crumb" }, [h("a", { href: "#/", text: "← Quest map" })]),
    h("h1", { text: zone.title }),
    h("p", { class: "lede", text: zone.tagline }),
    h("p", { class: "zone-progress",
             text: progress.total
               ? progress.passed + " of " + progress.total + " challenges cleared"
               : "This zone is mapped out but not built yet." })
  ]);

  var objectives = h("section", { class: "objectives" }, [
    h("h2", { text: "By the end of this zone you can" }),
    h("ul", {}, (zone.objectives || []).map(function (item) {
      return h("li", { text: item });
    }))
  ]);

  var lesson = h("section", { class: "lesson", html: zone.lesson || "" });

  var source = zone.source && zone.source.length
    ? h("p", { class: "zone-source", text: "Straight from the kit: " + zone.source.join(", ") })
    : null;

  var challenges = zone.challenges.length
    ? h("section", { class: "challenge-list" }, [
        h("h2", { text: "Challenges" }),
        h("ol", {}, zone.challenges.map(function (challenge, index) {
          return challengeRow(zone, challenge, index);
        }))
      ])
    : h("section", { class: "challenge-list stub" }, [
        h("h2", { text: "Planned challenges" }),
        h("ol", {}, (zone.plannedChallenges || []).map(function (title) {
          return h("li", { class: "planned", text: title });
        })),
        h("p", {
          class: "note",
          text: "Not built yet. site/CONTRIBUTING-CONTENT.md explains how to add "
            + "one - it is a single JSON file, no engine code."
        })
      ]);

  return h("div", { class: "view view-zone" },
           [head, objectives, lesson, source, challenges]);
}
