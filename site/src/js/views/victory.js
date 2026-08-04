/* The zone-cleared screen.
 *
 * Every other view is about what is still to do. This one is the only
 * place the site stops and says "look what you can do now" - which is
 * the whole reason for the XP and the badges in the first place. Clear a
 * zone and nobody tells you, and the game layer was decoration.
 *
 * Everything on it is READ from what actually happened: the XP is the XP
 * banked, the time is the time the runs took, the list of skills is the
 * zone's own objectives. Nothing here is congratulation the learner did
 * not earn.
 */

import { h } from "../dom.js";
import { Game } from "../game.js";
import { Store } from "../store.js";

/** Totals for one zone, added up from the per-challenge records. */
function tally(zone) {
  var xp = 0;
  var hints = 0;
  var seconds = 0;
  var firstTry = 0;
  var passed = 0;

  zone.challenges.forEach(function (challenge) {
    var record = Store.record(zone.id, challenge.id);
    if (record.status !== "passed") return;
    passed += 1;
    xp += record.xp || 0;
    hints += (record.hints || []).length;
    seconds += record.seconds || 0;
    if (record.attempts <= 1) firstTry += 1;
  });

  return {
    xp: xp, hints: hints, seconds: seconds, firstTry: firstTry,
    passed: passed, total: zone.challenges.length
  };
}

function readableTime(seconds) {
  if (!seconds) return "-";
  if (seconds < 60) return seconds + "s";
  var minutes = Math.round(seconds / 60);
  if (minutes < 60) return minutes + "m";
  return Math.floor(minutes / 60) + "h " + (minutes % 60) + "m";
}

function statTile(value, label) {
  return h("li", { class: "stat-tile" }, [
    h("strong", { text: value }),
    h("span", { text: label })
  ]);
}

/** The badge awarded for clearing this particular zone, if there is one. */
function zoneBadge(zone) {
  return Game.content.game.badges.filter(function (badge) {
    return badge.rule && badge.rule.type === "zoneCleared" && badge.rule.zone === zone.id;
  })[0];
}

function nextZone(content, zone) {
  return content.zones.filter(function (candidate) {
    return candidate.order > zone.order
      && !candidate.sideQuest
      && candidate.challenges.length;
  })[0];
}

export function renderVictory(content, zoneId) {
  var zone = content.zones.filter(function (z) { return z.id === zoneId; })[0];
  if (!zone) return h("p", { text: "No such zone." });

  var progress = Game.zoneProgress(zone.id);
  // Reachable by typing the URL, so it has to cope with not being true.
  if (!progress.complete) {
    return h("div", { class: "view view-victory" }, [
      h("div", { class: "victory-card" }, [
        h("p", { class: "eyebrow", text: "Not yet" }),
        h("h1", { text: zone.title + " is not cleared" }),
        h("p", { class: "lede",
          text: progress.passed + " of " + progress.total + " challenges done. "
            + "This page is waiting for you." }),
        h("p", { class: "victory-actions" }, [
          h("a", { class: "btn primary", href: "#/zone/" + zone.id,
                   text: "Back to " + zone.title })
        ])
      ])
    ]);
  }

  var totals = tally(zone);
  var badge = zoneBadge(zone);
  var next = nextZone(content, zone);

  var crest = h("div", { class: "victory-crest" }, [
    h("span", { class: "crest-abbr", text: zone.abbr || String(zone.order) }),
    h("span", { class: "crest-word", text: "Badge" })
  ]);

  var stats = h("ul", { class: "stat-tiles" }, [
    statTile("+" + totals.xp, "zone XP"),
    statTile(totals.passed + "/" + totals.total, "challenges"),
    statTile(String(totals.hints), totals.hints === 1 ? "hint spent" : "hints spent"),
    statTile(readableTime(totals.seconds), "time in zone")
  ]);

  // The objectives, now in the past tense. They were a promise on the
  // way in; here they are the receipt.
  var skills = (zone.objectives || []).length
    ? h("section", { class: "victory-panel" }, [
        h("p", { class: "panel-kind", text: "What you can do now" }),
        h("ul", { class: "skill-list" }, zone.objectives.map(function (item) {
          return h("li", {}, [
            h("span", { class: "skill-tick", "aria-hidden": "true", text: "✓" }),
            h("span", { text: item })
          ]);
        }))
      ])
    : null;

  var onwards = next
    ? h("section", { class: "victory-next" }, [
        h("span", { class: "next-mark", text: next.abbr || String(next.order) }),
        h("span", { class: "next-words" }, [
          h("strong", { text: "Next: " + next.title }),
          h("span", { class: "small muted", text: next.tagline })
        ])
      ])
    : null;

  var actions = h("p", { class: "victory-actions" }, [
    next
      ? h("a", { class: "btn primary", href: "#/zone/" + next.id,
                 text: "Enter " + next.title })
      : h("a", { class: "btn primary", href: "#/", text: "Back to the map" }),
    h("a", { class: "btn ghost", href: "#/", text: "Back to map" }),
    h("a", { class: "btn ghost", href: "#/badges", text: "See trophy case" })
  ]);

  return h("div", { class: "view view-victory" }, [
    h("div", { class: "victory-card" }, [
      h("p", { class: "eyebrow", text: "Zone cleared" }),
      crest,
      h("h1", { text: badge ? badge.name : zone.title + " cleared" }),
      h("p", { class: "lede victory-line",
        text: zone.title + " is behind you."
          + (totals.hints === 0 ? " Not one hint spent." : "")
          + (totals.firstTry === totals.total ? " Every challenge first try." : "") }),
      stats,
      skills,
      onwards,
      actions
    ])
  ]);
}
