/* The quest map: the home screen.
 *
 * It is an ordered list. On a wide screen CSS lifts each item onto a
 * drawn path; at 320 px the same list just flows down the page. That is
 * why the markup is a plain <ol> and not an SVG full of <text> - a map
 * you cannot tab through is a map half the learners cannot use.
 */

import { h, plural } from "../dom.js";
import { Game } from "../game.js";
import { Store } from "../store.js";

function statusOf(zone) {
  var progress = Game.zoneProgress(zone.id);
  if (progress.complete) return "complete";
  if (!Game.isUnlocked(zone)) return "locked";
  if (progress.passed > 0) return "started";
  return "open";
}

function pathBetween(zones) {
  // A single polyline through the zone centres, drawn behind the nodes.
  var points = zones.map(function (zone) {
    return (zone.map.x) + "," + (zone.map.y);
  }).join(" ");
  var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "map-path");
  svg.setAttribute("viewBox", "0 0 100 100");
  svg.setAttribute("preserveAspectRatio", "none");
  svg.setAttribute("aria-hidden", "true");
  var line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("points", points);
  svg.appendChild(line);
  return svg;
}

function zoneNode(zone) {
  var status = statusOf(zone);
  var progress = Game.zoneProgress(zone.id);
  var locked = status === "locked";

  var label = h("span", { class: "zone-label" }, [
    h("span", { class: "zone-index", text: zone.badge || String(zone.order) }),
    h("span", { class: "zone-title", text: zone.title })
  ]);

  var meta = h("span", { class: "zone-meta" }, [
    h("span", {
      text: locked ? Game.lockReason(zone)
        : progress.total
          ? progress.passed + " / " + progress.total + " cleared"
          : "Coming soon"
    })
  ]);

  var inner = [
    label,
    h("span", { class: "zone-tagline", text: zone.tagline }),
    meta
  ];

  var node = locked
    ? h("div", { class: "zone-node locked", "aria-disabled": "true" }, inner)
    : h("a", {
        class: "zone-node " + status,
        href: "#/zone/" + zone.id
      }, inner);

  return h("li", {
    class: "zone-item",
    style: "--x:" + zone.map.x + "%; --y:" + zone.map.y + "%"
  }, [node]);
}

export function renderMap(content) {
  var zones = content.zones;
  var passedCount = Object.keys(Store.data.challenges).filter(function (key) {
    return Store.data.challenges[key].status === "passed";
  }).length;
  var totalCount = zones.reduce(function (sum, z) { return sum + z.challenges.length; }, 0);

  var intro = h("section", { class: "map-intro" }, [
    h("h1", { text: "Quest for Automation" }),
    h("p", {
      class: "lede",
      text: "Learn Playwright and pytest by writing real Python that drives a "
        + "real shop, right here in the page. No install, no account, and every "
        + "line you write works unchanged in the kit's own test suite."
    }),
    h("p", { class: "map-stats" }, [
      h("strong", { text: plural(passedCount, "challenge", "challenges") + " cleared" }),
      h("span", { text: " of " + totalCount + " · " }),
      h("strong", { text: Store.data.xp + " XP" }),
      h("span", { text: " · " + Game.level(Store.data.xp).title })
    ])
  ]);

  var list = h("ol", { class: "quest-map" }, zones.map(zoneNode));
  var board = h("div", { class: "map-board" }, [pathBetween(zones), list]);

  return h("div", { class: "view view-map" }, [intro, board, legend()]);
}

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
