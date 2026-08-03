/* The quest map: the home screen.
 *
 * A trail of small circular nodes with their names written underneath,
 * rather than a grid of cards. That is not decoration - it is what lets
 * twelve zones share a screen and still leave the PATH as the thing you
 * see first. A card big enough to hold a tagline is big enough to
 * collide with its neighbour.
 *
 * Underneath it is still an ordered list of links. The SVG is scenery
 * (aria-hidden), the <ol> is the map: tab through it, read it with a
 * screen reader, or drop below 1100px and the positioning is simply
 * dropped and the same list flows down the page. A map you cannot tab
 * through is a map half the learners cannot use.
 *
 * The trail is DRAWN FROM the zone positions, not authored beside them.
 * Move a zone in its zone.json and the path follows it, because the one
 * thing worse than a hand-placed map is a hand-placed map plus a
 * hand-drawn path that disagrees with it.
 */

import { h, plural } from "../dom.js";
import { Game } from "../game.js";
import { Store } from "../store.js";

var SVG_NS = "http://www.w3.org/2000/svg";

function statusOf(zone) {
  var progress = Game.zoneProgress(zone.id);
  if (progress.complete) return "complete";
  if (!Game.isUnlocked(zone)) return "locked";
  if (progress.passed > 0) return "started";
  return "open";
}

// -------------------------------------------------------------- the trail

function svg(tag, attrs) {
  var node = document.createElementNS(SVG_NS, tag);
  Object.keys(attrs || {}).forEach(function (key) {
    node.setAttribute(key, attrs[key]);
  });
  return node;
}

/**
 * A smooth path through the given points (Catmull-Rom as cubic beziers).
 *
 * Straight lines between zones would read as a diagram; a curve reads as
 * a road. The control points are each a sixth of the way along the
 * neighbouring span, which is the standard tension that keeps the curve
 * from overshooting on a sharp turn.
 */
function curveThrough(points, from, to) {
  if (points.length < 2 || to <= from) return "";
  var d = "M " + points[from].x + " " + points[from].y;
  for (var i = from; i < to; i++) {
    var previous = points[Math.max(i - 1, 0)];
    var start = points[i];
    var end = points[i + 1];
    var next = points[Math.min(i + 2, points.length - 1)];
    var c1x = start.x + (end.x - previous.x) / 6;
    var c1y = start.y + (end.y - previous.y) / 6;
    var c2x = end.x - (next.x - start.x) / 6;
    var c2y = end.y - (next.y - start.y) / 6;
    d += " C " + c1x + " " + c1y + ", " + c2x + " " + c2y + ", " + end.x + " " + end.y;
  }
  return d;
}

function pointOf(zone) {
  return { x: zone.map.x, y: zone.map.y, zone: zone };
}

function nearest(point, candidates) {
  var best = null;
  var bestGap = Infinity;
  candidates.forEach(function (other) {
    var gap = Math.pow(other.x - point.x, 2) + Math.pow(other.y - point.y, 2);
    if (gap < bestGap) { bestGap = gap; best = other; }
  });
  return best;
}

/**
 * The scenery layer: contour rings, the main trail, and any side branch.
 *
 * preserveAspectRatio="none" lets the SVG share one coordinate system
 * with the nodes - both are plain percentages - so the path always meets
 * the circles exactly. The cost is that the drawing is stretched, which
 * is why every stroke carries vector-effect="non-scaling-stroke": the
 * line stays an even weight instead of turning into a wedge. The contour
 * rings are allowed to stretch into ovals, which is what a contour on a
 * map looks like anyway.
 */
function scenery(zones) {
  var board = svg("svg", {
    class: "map-scenery",
    viewBox: "0 0 100 100",
    preserveAspectRatio: "none",
    "aria-hidden": "true"
  });

  var main = zones.filter(function (zone) { return !zone.sideQuest; }).map(pointOf);
  var sides = zones.filter(function (zone) { return zone.sideQuest; }).map(pointOf);

  // Faint terrain under the trail. Placed off the path on purpose - they
  // are texture, and texture behind text is just noise.
  [[24, 30, 13], [62, 26, 9], [78, 62, 15], [34, 74, 11]].forEach(function (ring) {
    board.appendChild(svg("ellipse", {
      class: "map-contour", cx: ring[0], cy: ring[1], rx: ring[2], ry: ring[2] * 0.72,
      "vector-effect": "non-scaling-stroke"
    }));
  });

  // How far along the trail the learner has actually reached. The
  // segment INTO a zone is lit when that zone is open, so the bright
  // part of the road always ends at the next thing you can do.
  var frontier = 0;
  main.forEach(function (point, index) {
    if (Game.isUnlocked(point.zone)) frontier = index;
  });

  var ahead = curveThrough(main, frontier, main.length - 1);
  if (ahead) {
    board.appendChild(svg("path", {
      class: "trail trail-locked", d: ahead, "vector-effect": "non-scaling-stroke"
    }));
  }
  var travelled = curveThrough(main, 0, frontier);
  if (travelled) {
    board.appendChild(svg("path", {
      class: "trail trail-open", d: travelled, "vector-effect": "non-scaling-stroke"
    }));
  }

  // A side quest hangs off the nearest point of the main road, which is
  // exactly what it is: a detour you can take, not a gate you must pass.
  sides.forEach(function (side) {
    var anchor = nearest(side, main);
    if (!anchor) return;
    board.appendChild(svg("path", {
      class: "trail trail-side",
      d: "M " + anchor.x + " " + anchor.y + " L " + side.x + " " + side.y,
      "vector-effect": "non-scaling-stroke"
    }));
  });

  return board;
}

// --------------------------------------------------------------- the nodes

function nodeShape(zone) {
  // Shape carries meaning at a glance, before any text is read:
  // a circle is the road, a diamond is a detour, a square is the end.
  if (zone.sideQuest) return "diamond";
  if (zone.endgame) return "square";
  return "circle";
}

/**
 * The one line under a zone's name.
 *
 * Kept SHORT on purpose. "Clear The Form Marshes first." wraps to three
 * lines out on the trail and lands on top of the next zone's name - so
 * out there a locked zone just says "Locked", and the reason travels in
 * .zone-why, which only the stacked layout shows. The tooltip carries
 * it either way.
 */
function statusLine(zone, status) {
  var progress = Game.zoneProgress(zone.id);
  if (status === "locked") return "Locked";
  if (status === "complete") return "Cleared";
  if (!progress.total) return "Coming soon";
  if (status === "started") return progress.passed + " of " + progress.total + " done";
  return progress.total + " challenges";
}

function zoneNode(zone) {
  var status = statusOf(zone);
  var locked = status === "locked";

  var dot = h("span", { class: "zone-dot " + nodeShape(zone) }, [
    h("span", { class: "zone-abbr", text: zone.abbr || zone.badge || String(zone.order) }),
    status === "complete"
      ? h("span", { class: "zone-tick", "aria-hidden": "true", text: "✓" })
      : null
  ]);

  var reason = locked ? Game.lockReason(zone) : "";
  var label = h("span", { class: "zone-label" }, [
    h("span", { class: "zone-title", text: zone.title }),
    h("span", { class: "zone-state", text: statusLine(zone, status) }),
    reason ? h("span", { class: "zone-why", text: reason }) : null
  ]);

  var inner = [dot, label];
  var classes = "zone-node " + status + (zone.sideQuest ? " side" : "");

  // Locked zones are not links. Nothing to click beats a link that
  // looks disabled and still takes focus.
  var node = locked
    ? h("div", { class: classes, "aria-disabled": "true", title: reason }, inner)
    : h("a", { class: classes, href: "#/zone/" + zone.id }, inner);

  return h("li", {
    class: "zone-item",
    style: "--x:" + zone.map.x + "%; --y:" + zone.map.y + "%"
  }, [node]);
}

// ------------------------------------------------------------- the header

/** The first thing still to do: what "Continue" should open. */
function nextUp(content) {
  var found = null;
  content.zones.forEach(function (zone) {
    if (found || !Game.isUnlocked(zone)) return;
    zone.challenges.forEach(function (challenge) {
      if (found) return;
      if (!Store.isPassed(zone.id, challenge.id)) found = { zone: zone, challenge: challenge };
    });
  });
  return found;
}

function intro(content) {
  var next = nextUp(content);
  var cleared = Object.keys(Store.data.challenges).filter(function (key) {
    return Store.data.challenges[key].status === "passed";
  }).length;
  var total = content.zones.reduce(function (sum, z) { return sum + z.challenges.length; }, 0);
  var zonesIn = content.zones.filter(function (zone) {
    return Game.zoneProgress(zone.id).passed > 0;
  }).length;

  var actions = h("div", { class: "intro-actions" }, [
    next
      ? h("a", {
          class: "btn primary",
          href: "#/zone/" + next.zone.id + "/" + next.challenge.id,
          text: (cleared ? "Continue · " : "Start · ") + next.zone.title
        })
      : null,
    h("a", { class: "btn ghost", href: "#/badges", text: "Trophy case" })
  ]);

  return h("section", { class: "map-intro" }, [
    h("div", { class: "intro-words" }, [
      h("p", { class: "eyebrow", text: "Chapter I · Browser automation" }),
      h("h1", { text: "The road to a suite you trust" }),
      h("p", { class: "lede",
        text: "Twelve zones and one practice shop that breaks in all the ways real "
          + "apps do. Every line you write here works unchanged in the kit's own "
          + "test suite." }),
      h("p", { class: "map-stats" }, [
        h("strong", { text: plural(cleared, "challenge", "challenges") + " cleared" }),
        h("span", { text: " of " + total + " · " }),
        h("strong", { text: Store.data.xp + " XP" }),
        h("span", { text: " · " + Game.level(Store.data.xp).title
          + (zonesIn ? " · " + zonesIn + " zones in" : "") })
      ])
    ]),
    actions
  ]);
}

// ------------------------------------------------------- the status cards

/** How far along a countable badge is, so "chasing" can show a number. */
function badgeProgress(badge) {
  var rule = badge.rule;
  var passed = Object.keys(Store.data.challenges).filter(function (key) {
    return Store.data.challenges[key].status === "passed";
  });
  if (rule.type === "challengesPassed") return [passed.length, rule.value];
  if (rule.type === "statAtLeast") return [Store.data.stats[rule.stat] || 0, rule.value];
  if (rule.type === "firstTryPasses") {
    return [passed.filter(function (key) {
      return Store.data.challenges[key].attempts <= 1;
    }).length, rule.value];
  }
  if (rule.type === "passedWithoutHints") {
    return [passed.filter(function (key) {
      return !(Store.data.challenges[key].hints || []).length;
    }).length, rule.value];
  }
  return null;
}

function card(kind, title, body) {
  return h("li", { class: "status-card" }, [
    h("p", { class: "card-kind", text: kind }),
    h("p", { class: "card-title", text: title }),
    h("p", { class: "card-body", text: body })
  ]);
}

function statusCards(content) {
  var cards = [];

  var next = nextUp(content);
  if (next) {
    cards.push(card("Up next", next.challenge.title,
      next.zone.title + " · " + next.challenge.xp + " XP on the table."));
  }

  var days = Store.data.streak.days;
  cards.push(card("Daily run",
    days > 1 ? days + "-day streak" : "Day one",
    days > 1
      ? "It holds as long as one test goes green before midnight."
      : "Clear a challenge today and the streak starts counting."));

  var chasing = content.game.badges.filter(function (badge) {
    return !Store.data.badges[badge.id];
  })[0];
  if (chasing) {
    var progress = badgeProgress(chasing);
    // Clamped: a badge can be sitting at "earned but not yet awarded"
    // for a moment, and "18 of 1" reads like a bug because it is one.
    var counter = progress
      ? " · " + Math.min(progress[0], progress[1]) + " of " + progress[1]
      : "";
    cards.push(card("Chasing", chasing.name + counter, chasing.hint));
  }

  return h("ul", { class: "status-cards" }, cards);
}

// -------------------------------------------------------------- assembly

function legend() {
  var items = [
    ["open", "Open - go for it"],
    ["started", "In progress"],
    ["complete", "Cleared"],
    ["locked", "Locked until you clear what it needs"]
  ];
  return h("ul", { class: "map-legend" }, items.map(function (pair) {
    return h("li", {}, [
      h("span", { class: "swatch " + pair[0], "aria-hidden": "true" }),
      h("span", { text: pair[1] })
    ]);
  }));
}

export function renderMap(content) {
  var zones = content.zones;
  var board = h("div", { class: "map-board" }, [
    scenery(zones),
    h("ol", { class: "quest-map" }, zones.map(zoneNode)),
    legend()
  ]);

  return h("div", { class: "view view-map" }, [
    intro(content),
    board,
    statusCards(content)
  ]);
}
