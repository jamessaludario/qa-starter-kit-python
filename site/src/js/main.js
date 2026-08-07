/* Boot, header, and the router.
 *
 * A hash router, not the History API: the site has to work when it is
 * served as a folder of files from GitHub Pages, where there is no
 * server to rewrite /zone/locator-forest back to index.html.
 */

import { announce, clear, h, qs } from "./dom.js";
import { Game } from "./game.js";
import { Store } from "./store.js";
import { renderChallenge } from "./views/challenge.js";
import { renderMap } from "./views/map.js";
import { renderVictory } from "./views/victory.js";
import { renderZone } from "./views/zone.js";

var content = window.QUEST_CONTENT;

function navigate(path) {
  window.location.hash = "#" + path;
}

// ------------------------------------------------------------------ header

/** Comma-grouped, so 1180 reads as 1,180 at a glance. */
function grouped(value) {
  return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function navLink(href, label, active) {
  return h("a", {
    href: href, text: label,
    // aria-current is what tells a screen reader which tab you are on;
    // the bold weight is only the sighted half of the same statement.
    "aria-current": active ? "page" : null
  });
}

function header(route) {
  var xp = Store.data.xp;
  var level = Game.level(xp);
  var here = route[0] || "map";

  var nav = h("nav", { class: "hud-links", "aria-label": "Sections" }, [
    navLink("#/", "Map", here === "map"),
    navLink("#/badges", "Trophies", here === "badges"),
    navLink("#/progress", "Profile", here === "progress"),
    navLink("#/about", "About", here === "about")
  ]);

  var bar = h("div", {
    class: "hud-bar", role: "progressbar",
    "aria-valuenow": String(Math.round(level.progress * 100)),
    "aria-valuemin": "0", "aria-valuemax": "100",
    "aria-label": level.next ? "Progress to " + level.next.title : "Top level reached"
  }, [
    h("div", { class: "hud-bar-fill", style: "width:" + (level.progress * 100) + "%" })
  ]);

  // "1,180 / 1,600" beats a bare "1,180": a bar with no numbers cannot
  // tell you how much further, which is the only question it is asked.
  var counter = level.next
    ? grouped(xp) + " / " + grouped(level.next.xp)
    : grouped(xp) + " XP";

  return h("header", { class: "site-header" }, [
    h("div", { class: "header-left" }, [
      h("a", { class: "brand", href: "#/" }, [
        h("span", { class: "brand-mark", "aria-hidden": "true", text: "▲" }),
        h("span", { text: "Quest for Automation" })
      ]),
      nav
    ]),
    h("div", { class: "hud" }, [
      h("span", { class: "hud-level", text: "LV " + (level.index + 1) }),
      h("span", { class: "hud-title", text: level.title }),
      bar,
      h("span", { class: "hud-xp", text: counter }),
      Store.data.streak.days > 1
        ? h("span", { class: "hud-streak", title: "Day streak" }, [
            h("span", { "aria-hidden": "true", text: "▲" }),
            h("span", { text: Store.data.streak.days + "d" })
          ])
        : null,
      accentPicker(),
      themeToggle()
    ])
  ]);
}

// ------------------------------------------------------------------- theme

var THEME_KEY = "quest-for-automation.theme";

function systemTheme() {
  return window.matchMedia
    && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function savedTheme() {
  try { return window.localStorage.getItem(THEME_KEY); } catch (error) { return null; }
}

/**
 * Put the resolved theme on <html>.
 *
 * Resolved in JS rather than by a media query so an explicit choice and
 * the system default use the same mechanism - otherwise the toggle and
 * the OS end up fighting over CSS specificity.
 */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme || systemTheme());
}

// ------------------------------------------------------------------ accent

var ACCENT_KEY = "quest-for-automation.accent";

// Curated PAIRS, not a colour wheel. The site uses two accents with
// jobs - the road, and the detour off it - and each pair has to stay
// readable in both themes on two very different grounds. Most
// combinations a free colour picker would allow fail that in one theme
// or the other, which is why this is a short list.
var ACCENTS = [
  ["mint", "Mint"],
  ["amber", "Amber"],
  ["azure", "Azure"],
  ["violet", "Violet"],
  ["rose", "Rose"]
];

function savedAccent() {
  try {
    var value = window.localStorage.getItem(ACCENT_KEY);
    return ACCENTS.some(function (a) { return a[0] === value; }) ? value : "mint";
  } catch (error) { return "mint"; }
}

function applyAccent(accent) {
  // "mint" is the stylesheet's own palette, so it carries no attribute
  // at all - one less selector to keep in step with the base rules.
  if (!accent || accent === "mint") {
    document.documentElement.removeAttribute("data-accent");
  } else {
    document.documentElement.setAttribute("data-accent", accent);
  }
}

function accentPicker() {
  var current = savedAccent();
  var select = h("select", {
    class: "accent-select", id: "accent-select",
    onchange: function (event) {
      var value = event.target.value;
      try { window.localStorage.setItem(ACCENT_KEY, value); } catch (error) { /* no storage */ }
      applyAccent(value);
    }
  }, ACCENTS.map(function (a) {
    return h("option", { value: a[0], text: a[1], selected: a[0] === current || null });
  }));

  return h("label", { class: "accent-picker", for: "accent-select" }, [
    h("span", { class: "accent-picker-label", text: "Accent" }),
    select
  ]);
}

function themeToggle() {
  var current = savedTheme() || systemTheme();
  var next = current === "dark" ? "light" : "dark";
  return h("button", {
    class: "theme-toggle", type: "button",
    "aria-label": "Switch to the " + next + " theme",
    onclick: function () {
      try { window.localStorage.setItem(THEME_KEY, next); } catch (error) { /* no storage */ }
      applyTheme(next);
      render();
    }
  }, [next]);
}

// ------------------------------------------------------------- extra views

function renderBadges() {
  var owned = Store.data.badges;
  return h("div", { class: "view view-badges" }, [
    h("p", { class: "crumb" }, [h("a", { href: "#/", text: "← Quest map" })]),
    h("h1", { text: "Badges" }),
    h("p", { class: "lede",
             text: "Each one marks a habit worth having, not a number worth chasing." }),
    h("ul", { class: "badge-grid" }, content.game.badges.map(function (badge) {
      var earned = owned[badge.id];
      return h("li", { class: "badge-card" + (earned ? " earned" : "") }, [
        h("span", { class: "badge-icon", "aria-hidden": "true", text: badge.icon || "★" }),
        h("strong", { text: badge.name }),
        h("span", { class: "badge-hint", text: badge.hint }),
        h("span", { class: "badge-state", text: earned ? "Earned " + earned : "Not yet" })
      ]);
    }))
  ]);
}

function renderProgress() {
  var status = h("p", { class: "small muted", "aria-live": "polite" });

  var download = h("button", { class: "btn primary", type: "button", onclick: function () {
    var url = URL.createObjectURL(Store.exportBlob());
    var link = h("a", { href: url, download: "quest-progress.json" });
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    status.textContent = "Saved quest-progress.json.";
  } }, ["Export my progress"]);

  var file = h("input", { type: "file", accept: "application/json", class: "file-input",
                          id: "import-file" });
  file.addEventListener("change", function () {
    var chosen = file.files[0];
    if (!chosen) return;
    chosen.text().then(function (text) {
      Store.importText(text);
      status.textContent = "Imported. Your progress is now " + Store.data.xp + " XP.";
      render();
    }).catch(function (error) {
      status.textContent = "Could not import that file: " + error.message;
    });
  });

  var reset = h("button", { class: "btn danger", type: "button", onclick: function () {
    if (window.confirm("Erase all XP, badges and cleared challenges? This cannot be undone.")) {
      Store.reset();
      status.textContent = "Progress erased.";
      render();
    }
  } }, ["Erase everything"]);

  return h("div", { class: "view view-profile" }, [
    profileHead(),
    h("div", { class: "profile-grid" }, [habitsPanel(), zoneCompletion()]),
    trophyCase(),
    h("section", { class: "rail-card profile-data" }, [
      h("p", { class: "panel-kind", text: "Your data" }),
      h("p", { class: "small muted",
               text: "Everything lives in this browser's local storage. No account, "
                 + "no server, nothing sent anywhere. Which also means: clear your "
                 + "browser data and it is gone, so export a copy if it matters." }),
      h("div", { class: "toolbar" }, [
        download,
        h("label", { class: "btn ghost", for: "import-file" }, ["Import a file"]),
        file,
        reset
      ]),
      status
    ])
  ]);
}

/** Total seconds recorded across every cleared challenge. */
function timeInvested() {
  return Object.keys(Store.data.challenges).reduce(function (sum, key) {
    return sum + (Store.data.challenges[key].seconds || 0);
  }, 0);
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

function profileHead() {
  var xp = Store.data.xp;
  var level = Game.level(xp);
  var badgeCount = Object.keys(Store.data.badges).length;
  var started = Store.data.startedAt
    ? new Date(Store.data.startedAt).toLocaleDateString(undefined,
        { day: "numeric", month: "long", year: "numeric" })
    : "today";

  return h("section", { class: "profile-head" }, [
    h("div", { class: "profile-id" }, [
      // No name, because there is no account to put one in. The level
      // IS the identity here, which is also the honest thing to show.
      h("span", { class: "profile-mark", text: "LV " + (level.index + 1) }),
      h("div", {}, [
        h("h1", { text: level.title }),
        h("p", { class: "profile-since",
                 text: "Started " + started + " · " + Store.data.streak.days
                   + "-day streak" }),
        h("div", { class: "hud-bar profile-bar" }, [
          h("div", { class: "hud-bar-fill",
                     style: "width:" + (level.progress * 100) + "%" })
        ]),
        h("p", { class: "profile-next", text: level.next
          ? grouped(xp) + " / " + grouped(level.next.xp) + " XP to " + level.next.title
          : grouped(xp) + " XP · top level" })
      ])
    ]),
    h("ul", { class: "stat-tiles" }, [
      statTile(grouped(xp), "total XP"),
      statTile(readableTime(timeInvested()), "time invested"),
      statTile(String(Store.data.stats.runs), "test runs"),
      statTile(badgeCount + " / " + content.game.badges.length, "badges")
    ])
  ]);
}

/**
 * Habits, counted from what the learner actually ran.
 *
 * Deliberately NOT a skills radar with invented axes. These four are
 * real counters kept by the runner, and each one names a habit the kit
 * argues for - which makes them worth showing and worth moving.
 */
function habitsPanel() {
  var stats = Store.data.stats;
  var passed = Object.keys(Store.data.challenges).filter(function (key) {
    return Store.data.challenges[key].status === "passed";
  });
  var firstTry = passed.filter(function (key) {
    return Store.data.challenges[key].attempts <= 1;
  }).length;

  var rows = [
    ["Role-based locators used", stats.roleLocators,
     "The top of the priority order, and the ones that survive a redesign."],
    ["Clean reviews", stats.cleanRuns,
     "Passes with no advisory findings at all."],
    ["First-try passes", firstTry,
     "Read the failure, then wrote the fix - out of " + passed.length + " cleared."],
    ["Sleeps caught", stats.sleepAttempts,
     "Attempts the reviewer stopped before they ran. Not a score to be ashamed of."]
  ];

  return h("section", { class: "rail-card" }, [
    h("p", { class: "panel-kind", text: "Habits" }),
    h("p", { class: "small muted",
             text: "Counted from the code you actually ran, not from lessons opened." }),
    h("ul", { class: "habit-list" }, rows.map(function (row) {
      return h("li", {}, [
        h("span", { class: "habit-value", text: String(row[1]) }),
        h("span", { class: "habit-words" }, [
          h("strong", { text: row[0] }),
          h("span", { class: "small muted", text: row[2] })
        ])
      ]);
    }))
  ]);
}

function zoneCompletion() {
  return h("section", { class: "rail-card" }, [
    h("p", { class: "panel-kind", text: "Zone completion" }),
    h("ul", { class: "zone-bars" }, content.zones.map(function (zone) {
      var progress = Game.zoneProgress(zone.id);
      var percent = progress.total
        ? Math.round(progress.passed / progress.total * 100) : 0;
      var note = progress.total
        ? percent + "%"
        : (zone.sideQuest ? "side" : "-");
      return h("li", { class: progress.passed ? "" : "untouched" }, [
        h("a", { class: "zone-bar-name", href: "#/zone/" + zone.id, text: zone.title }),
        h("span", { class: "zone-bar" }, [
          h("span", { class: "zone-bar-fill", style: "width:" + percent + "%" })
        ]),
        h("span", { class: "zone-bar-note", text: note })
      ]);
    }))
  ]);
}

function trophyCase() {
  var owned = Store.data.badges;
  var earned = content.game.badges.filter(function (b) { return owned[b.id]; }).length;

  return h("section", { class: "rail-card" }, [
    h("p", { class: "panel-kind" }, [
      h("span", { text: "Trophy case" }),
      h("span", { class: "hints-spent",
                  text: earned + " earned · " + (content.game.badges.length - earned)
                    + " to chase" })
    ]),
    h("ul", { class: "badge-grid" }, content.game.badges.map(function (badge) {
      var when = owned[badge.id];
      return h("li", { class: "badge-card" + (when ? " earned" : "") }, [
        h("span", { class: "badge-icon", "aria-hidden": "true", text: badge.icon || "★" }),
        h("strong", { text: badge.name }),
        h("span", { class: "badge-hint", text: badge.hint }),
        h("span", { class: "badge-state", text: when ? "Earned " + when : "Not yet" })
      ]);
    }))
  ]);
}

function renderAbout() {
  return h("div", { class: "view view-about", html: content.about });
}

// ---------------------------------------------------------------- routing

function parseHash() {
  var raw = window.location.hash.replace(/^#\/?/, "");
  return raw.split("/").filter(Boolean);
}

function render() {
  var parts = parseHash();
  var root = qs("#app");
  clear(root);
  root.appendChild(header(parts));

  var main = h("main", { id: "main", tabindex: "-1" });
  root.appendChild(main);

  if (parts[0] === "cleared" && parts[1]) {
    main.appendChild(renderVictory(content, parts[1]));
  } else if (parts[0] === "zone" && parts[2]) {
    main.appendChild(renderChallenge(content, parts[1], parts[2], navigate));
  } else if (parts[0] === "zone" && parts[1]) {
    main.appendChild(renderZone(content, parts[1]));
  } else if (parts[0] === "badges") {
    main.appendChild(renderBadges());
  } else if (parts[0] === "progress") {
    main.appendChild(renderProgress());
  } else if (parts[0] === "about") {
    main.appendChild(renderAbout());
  } else {
    main.appendChild(renderMap(content));
  }

  root.appendChild(h("footer", { class: "site-footer" }, [
    h("p", {}, [
      h("span", { text: "Part of the " }),
      h("a", { href: "https://github.com/jamessaludario/qa-starter-kit-python",
               text: "QA starter kit" }),
      h("span", { text: ". Everything runs in this tab: no account, no server, "
                        + "nothing uploaded." })
    ])
  ]));
}

// ------------------------------------------------------------------- boot

Store.load();
Game.init(content);
applyTheme(savedTheme());
applyAccent(savedAccent());

// Follow the system only while the learner has expressed no preference
// of their own. Once they pick, their pick wins.
if (window.matchMedia) {
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    if (!savedTheme()) { applyTheme(null); }
  });
}

window.addEventListener("hashchange", function () {
  render();
  var main = qs("#main");
  if (main) main.focus();
  window.scrollTo(0, 0);
});
window.addEventListener("quest:progress", function () {
  // Keep the XP bar honest without redrawing the challenge you are on.
  var current = qs(".site-header");
  if (current) current.replaceWith(header(parseHash()));
});
render();
announce("Quest map loaded");

// Offline after the first visit. Registration failing is not an error
// worth showing anyone - the site simply stays online-only.
if ("serviceWorker" in navigator && window.location.protocol.indexOf("http") === 0) {
  navigator.serviceWorker.register("sw.js").catch(function () {});
}
