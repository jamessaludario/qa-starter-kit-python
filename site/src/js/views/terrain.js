/* Map backgrounds: five grounds for the same trail, plus the picker.
 *
 * The map already had one ground - a blueprint grid with the wireframes
 * of web pages laid on it - and it is still the default, because it is
 * the only one that says something true about the journey: the quest is
 * through PAGES, not mountains. The other four exist because a learner
 * looks at this screen more than any other, and letting them choose the
 * scenery is the cheapest fun in the product.
 *
 * All five are built once and switched with a data attribute on
 * .map-board, so changing ground is a class flip rather than a re-render
 * of the trail. Every layer is aria-hidden scenery: if you find yourself
 * reading it, it is too strong.
 *
 * Coordinates are the same 0-100 space as the zones (see scenery() in
 * views/map.js), and the board is stretched to its own aspect ratio, so
 * every stroke carries vector-effect="non-scaling-stroke" and NOTHING
 * here uses <svg:text> - text in this space gets stretched into a wedge.
 * The flavour lines are HTML captions instead.
 *
 * Positions avoid the zone coordinates in content/zones/*\/zone.json and
 * sit in the three gaps the trail leaves, the same ones the wireframes
 * were placed against.
 */

import { h } from "../dom.js";

var SVG_NS = "http://www.w3.org/2000/svg";
var KEY = "quest-for-automation.terrain";

export var TERRAINS = [
  ["blueprint", "Blueprint — pages", "The ground is the pages you will be testing."],
  ["survey", "Survey chart", "Ruled plate with grid refs, coastline and a compass."],
  ["contours", "Contours", "Elevation rings: the zones read as high and low ground."],
  ["terminal", "Terminal", "Scanlines and plotted axes — the map as a test run."],
  ["night", "Constellation", "A star field, with the route drawn between the stars."],
  ["flat", "Flat", "Nothing behind the trail. The quietest option."]
];

function svg(tag, attrs) {
  var node = document.createElementNS(SVG_NS, tag);
  Object.keys(attrs || {}).forEach(function (key) {
    node.setAttribute(key, attrs[key]);
  });
  return node;
}

/** A stroked shape in map space: even weight however the board stretches. */
function stroked(tag, attrs) {
  var node = svg(tag, attrs);
  node.setAttribute("vector-effect", "non-scaling-stroke");
  return node;
}

function group(kind, children) {
  var g = svg("g", { class: "terrain-layer t-" + kind, "aria-hidden": "true" });
  (children || []).forEach(function (child) { if (child) g.appendChild(child); });
  return g;
}

// ------------------------------------------------------------ the grounds

/* 1. Blueprint. Unchanged from the original terrain(): graph paper with
 * the faint wireframes of a product grid, a form and a cart on it. Built
 * in views/map.js, which owns the wireframes; this module just wraps
 * whatever it hands over so the switcher can hide it like the rest. */
export function blueprint(existingGroup) {
  var g = group("blueprint");
  if (existingGroup) {
    while (existingGroup.firstChild) g.appendChild(existingGroup.firstChild);
  }
  return g;
}

/* 2. Survey chart. The most cartographic of the five and the one that
 * makes the board feel like a PLACE: a ruled plate, ticked margins, a
 * hatched coastline along the empty left flank, ridge hatching in the
 * top-centre gap, and a compass rose in the one corner no zone uses.
 * Warm gold throughout, because that is already the map's "this is
 * scenery, not the road" colour. */
export function survey() {
  var kids = [];
  var defs = svg("defs", {});
  var hatch = svg("pattern", {
    id: "qfa-t-hatch", width: "1.6", height: "1.6",
    patternUnits: "userSpaceOnUse", patternTransform: "rotate(35)"
  });
  hatch.appendChild(svg("line", { x1: 0, y1: 0, x2: 0, y2: 1.6, class: "t-hatch-line" }));
  defs.appendChild(hatch);
  kids.push(defs);

  kids.push(svg("rect", { x: 0, y: 0, width: 100, height: 100, class: "t-wash" }));

  // Ruled to a 10-unit grid, which is coarse enough to read as a survey
  // plate rather than graph paper.
  for (var n = 10; n < 100; n += 10) {
    kids.push(stroked("line", { x1: n, y1: 3, x2: n, y2: 97, class: "t-rule" }));
    kids.push(stroked("line", { x1: 3, y1: n, x2: 97, y2: n, class: "t-rule" }));
  }

  // Ticked margins. Grid-ref LETTERS would be better still, but they
  // belong in HTML - see captions() - because svg text stretches.
  for (var t = 5; t < 100; t += 10) {
    kids.push(stroked("line", { x1: t, y1: 2.2, x2: t, y2: 4.4, class: "t-tick" }));
    kids.push(stroked("line", { x1: 2.2, y1: t, x2: 4.4, y2: t, class: "t-tick" }));
  }

  // The coastline runs through the empty left flank and off the bottom
  // edge: the one large area with no zone in it.
  var coast = "M 0 62 C 8 59, 16 65, 24 70 C 32 75, 38 82, 41 100";
  kids.push(svg("path", { d: coast + " L 0 100 Z", class: "t-water", fill: "url(#qfa-t-hatch)" }));
  kids.push(stroked("path", { d: coast, class: "t-coast", fill: "none" }));

  // Ridge hatching in the top-centre gap.
  kids.push(stroked("path", { d: "M 44 20 L 50 13 L 56 19 L 62 12 L 68 18", class: "t-ridge", fill: "none" }));
  kids.push(stroked("path", { d: "M 47 23 L 50 18 L 54 22", class: "t-ridge", fill: "none" }));
  kids.push(stroked("path", { d: "M 59 22 L 62 17 L 66 21", class: "t-ridge", fill: "none" }));

  // Double border, the way a printed plate is trimmed.
  kids.push(stroked("rect", { x: 2, y: 2, width: 96, height: 96, class: "t-frame", fill: "none" }));
  kids.push(stroked("rect", { x: 3.4, y: 3.4, width: 93.2, height: 93.2, class: "t-frame-thin", fill: "none" }));

  // Compass rose, bottom-left: the legend owns bottom-right and the
  // trail owns everything between them.
  var rose = svg("g", { class: "t-compass", transform: "translate(9 88)" });
  rose.appendChild(stroked("circle", { cx: 0, cy: 0, r: 4.2, fill: "none" }));
  rose.appendChild(svg("path", { d: "M 0 -6.4 L 1.1 0 L 0 6.4 L -1.1 0 Z", class: "t-rose-ns" }));
  rose.appendChild(svg("path", { d: "M -6.4 0 L 0 -1.1 L 6.4 0 L 0 1.1 Z", class: "t-rose-ew" }));
  kids.push(rose);

  return group("survey", kids);
}

/* 3. Contours. Elevation rings around the three gaps, so the trail reads
 * as crossing high and low ground. Deliberately allowed to stretch into
 * ovals - that is what a contour on a map looks like anyway. */
export function contours() {
  var kids = [];
  var defs = svg("defs", {});
  var pattern = svg("pattern", {
    id: "qfa-t-dots", width: "4", height: "6", patternUnits: "userSpaceOnUse"
  });
  pattern.appendChild(svg("circle", { cx: "0.4", cy: "0.4", r: "0.16", class: "grid-dot" }));
  defs.appendChild(pattern);
  kids.push(defs);
  kids.push(svg("rect", { x: 0, y: 0, width: 100, height: 100, fill: "url(#qfa-t-dots)" }));

  // [cx, cy, rx, ry] per hill, then three rings each.
  [[14, 58, 15, 13], [39, 60, 18, 12], [52, 14, 14, 9], [86, 78, 16, 14]]
    .forEach(function (hill) {
      [1, 0.66, 0.36].forEach(function (scale) {
        kids.push(stroked("ellipse", {
          cx: hill[0], cy: hill[1],
          rx: (hill[2] * scale).toFixed(2), ry: (hill[3] * scale).toFixed(2),
          class: "t-contour", fill: "none"
        }));
      });
    });

  return group("contours", kids);
}

/* 4. Terminal. The dev-tool read of the same map: scanlines, a plotted
 * pair of axes with ticks, and a dashed plot frame. For the QA engineer
 * who wants the game to look like their day job. */
export function terminal() {
  var kids = [];
  var defs = svg("defs", {});
  var scan = svg("pattern", {
    id: "qfa-t-scan", width: "2", height: "1.4", patternUnits: "userSpaceOnUse"
  });
  scan.appendChild(svg("rect", { x: 0, y: 0, width: 2, height: 0.5, class: "t-scanline" }));
  defs.appendChild(scan);
  kids.push(defs);
  kids.push(svg("rect", { x: 0, y: 0, width: 100, height: 100, fill: "url(#qfa-t-scan)" }));

  kids.push(stroked("line", { x1: 5, y1: 5, x2: 5, y2: 95, class: "t-axis" }));
  kids.push(stroked("line", { x1: 5, y1: 95, x2: 95, y2: 95, class: "t-axis" }));
  for (var n = 15; n < 95; n += 10) {
    kids.push(stroked("line", { x1: n, y1: 93.6, x2: n, y2: 96.4, class: "t-tick" }));
    kids.push(stroked("line", { x1: 3.6, y1: n, x2: 6.4, y2: n, class: "t-tick" }));
  }
  kids.push(stroked("rect", {
    x: 5, y: 5, width: 90, height: 90, class: "t-plot", fill: "none",
    "stroke-dasharray": "0.6 1.6"
  }));

  return group("terminal", kids);
}

/* 5. Constellation. A star field with the route drawn between stars.
 * The most fun and the least useful: it is the one ground that competes
 * with the mint trail for "glowing dot", so the stars are kept dim and
 * the joining lines are grey rather than accent. */
export function night() {
  var kids = [];
  kids.push(svg("ellipse", { cx: 30, cy: 22, rx: 34, ry: 26, class: "t-glow quest" }));
  kids.push(svg("ellipse", { cx: 79, cy: 66, rx: 30, ry: 25, class: "t-glow side" }));

  // [x, y, r]. Scattered wide - a star is small enough to sit under a
  // label without arguing with it.
  [[9, 8, .45], [17, 33, .3], [22, 6, .5], [30, 38, .34], [36, 13, .42],
   [44, 45, .3], [49, 19, .55], [55, 9, .32], [61, 49, .4], [68, 13, .32],
   [74, 40, .48], [81, 22, .3], [88, 34, .42], [95, 15, .3], [12, 55, .45],
   [20, 71, .3], [27, 92, .4], [34, 65, .28], [42, 84, .5], [50, 63, .3],
   [58, 93, .4], [65, 76, .28], [73, 90, .45], [83, 78, .3], [90, 93, .4],
   [96, 71, .3], [6, 44, .32], [64, 30, .3]]
    .forEach(function (star) {
      kids.push(svg("circle", { cx: star[0], cy: star[1], r: star[2], class: "t-star" }));
    });

  [ "M 22 6 L 36 13 L 49 19 L 55 9",
    "M 74 40 L 88 34 L 81 22 L 68 13",
    "M 42 84 L 58 93 L 73 90" ].forEach(function (d) {
      kids.push(stroked("path", { d: d, class: "t-constellation", fill: "none" }));
    });

  return group("night", kids);
}

// ------------------------------------------------------------- the layers

/**
 * Every ground, built once, for the switcher to flip between.
 *
 * `existing` is the <g> that views/map.js already builds for the
 * blueprint - passing it in keeps ownership of the page wireframes where
 * it was instead of copying them here.
 */
export function terrainLayers(existing) {
  return [blueprint(existing), survey(), contours(), terminal(), night()];
}

/**
 * The flavour lines, as HTML.
 *
 * In the board rather than the SVG on purpose: the board is stretched to
 * its own aspect ratio, so anything typographic has to sit outside that
 * coordinate system to stay the shape the type designer drew it.
 */
export function terrainCaptions() {
  return h("div", { class: "terrain-captions", "aria-hidden": "true" }, [
    h("p", { class: "terrain-caption for-survey", text: "Plate I · Chapter I · scale 1:1 zone" }),
    h("p", { class: "terrain-caption for-terminal", text: "$ pytest tour-tests/ -q  # 12 zones collected" }),
    h("p", { class: "terrain-caption for-night", text: "The route, as a constellation" })
  ]);
}

// ------------------------------------------------------------- the picker

export function savedTerrain() {
  try {
    var value = window.localStorage.getItem(KEY);
    return TERRAINS.some(function (t) { return t[0] === value; }) ? value : "blueprint";
  } catch (error) {
    return "blueprint";
  }
}

function saveTerrain(value) {
  try { window.localStorage.setItem(KEY, value); } catch (error) { /* no storage */ }
}

/**
 * A labelled <select>, next to "Trophy case".
 *
 * A row of buttons would be prettier and would also be six more things
 * between the learner and the map. A select is one control, is keyboard
 * and screen-reader native for free, and collapses to nothing at 320px -
 * where the trail is hidden anyway and the ground is not being drawn.
 *
 * Changing it flips a data attribute on .map-board. No re-render: the
 * trail, the nodes and the progress are all untouched by a change of
 * scenery, and re-rendering them would restart the road's animation for
 * no reason.
 */
export function terrainPicker() {
  var current = savedTerrain();

  var select = h("select", {
    class: "terrain-select", id: "terrain-select",
    onchange: function (event) {
      var value = event.target.value;
      saveTerrain(value);
      var board = document.querySelector(".map-board");
      if (board) board.dataset.terrain = value;
    }
  }, TERRAINS.map(function (t) {
    return h("option", { value: t[0], text: t[1], selected: t[0] === current || null,
                         title: t[2] });
  }));

  return h("label", { class: "terrain-picker", for: "terrain-select" }, [
    h("span", { class: "terrain-picker-label", text: "Terrain" }),
    select
  ]);
}
