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
import { renderZone } from "./views/zone.js";

var content = window.QUEST_CONTENT;

function navigate(path) {
  window.location.hash = "#" + path;
}

// ------------------------------------------------------------------ header

function header() {
  var xp = Store.data.xp;
  var level = Game.level(xp);
  var badgeCount = Object.keys(Store.data.badges).length;

  return h("header", { class: "site-header" }, [
    h("a", { class: "brand", href: "#/" }, [
      h("span", { class: "brand-mark", "aria-hidden": "true", text: "▲" }),
      h("span", { text: "Quest for Automation" })
    ]),
    h("div", { class: "hud" }, [
      h("div", { class: "hud-level" }, [
        h("span", { class: "hud-title", text: level.title }),
        h("span", { class: "hud-xp", text: xp + " XP" })
      ]),
      h("div", {
        class: "hud-bar", role: "progressbar",
        "aria-valuenow": String(Math.round(level.progress * 100)),
        "aria-valuemin": "0", "aria-valuemax": "100",
        "aria-label": level.next
          ? "Progress to " + level.next.title
          : "Top level reached"
      }, [
        h("div", { class: "hud-bar-fill", style: "width:" + (level.progress * 100) + "%" })
      ]),
      h("nav", { class: "hud-links" }, [
        h("a", { href: "#/badges", text: "Badges (" + badgeCount + ")" }),
        h("a", { href: "#/progress", text: "Progress" }),
        h("a", { href: "#/about", text: "About" })
      ])
    ])
  ]);
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

  return h("div", { class: "view view-progress" }, [
    h("p", { class: "crumb" }, [h("a", { href: "#/", text: "← Quest map" })]),
    h("h1", { text: "Your progress" }),
    h("p", { class: "lede",
             text: "Everything lives in this browser's local storage. No account, "
               + "no server, nothing sent anywhere. Which also means: clear your "
               + "browser data and it is gone, so export a copy if it matters." }),
    h("dl", { class: "stat-list" }, [
      h("dt", { text: "XP" }), h("dd", { text: String(Store.data.xp) }),
      h("dt", { text: "Level" }), h("dd", { text: Game.level(Store.data.xp).title }),
      h("dt", { text: "Runs" }), h("dd", { text: String(Store.data.stats.runs) }),
      h("dt", { text: "Day streak" }), h("dd", { text: String(Store.data.streak.days) }),
      h("dt", { text: "Role-based locators used" }),
      h("dd", { text: String(Store.data.stats.roleLocators) })
    ]),
    h("div", { class: "toolbar" }, [
      download,
      h("label", { class: "btn ghost", for: "import-file" }, ["Import a file"]),
      file,
      reset
    ]),
    status
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
  root.appendChild(header());

  var main = h("main", { id: "main", tabindex: "-1" });
  root.appendChild(main);

  if (parts[0] === "zone" && parts[2]) {
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
window.addEventListener("hashchange", function () {
  render();
  var main = qs("#main");
  if (main) main.focus();
  window.scrollTo(0, 0);
});
window.addEventListener("quest:progress", function () {
  // Keep the XP bar honest without redrawing the challenge you are on.
  var current = qs(".site-header");
  if (current) current.replaceWith(header());
});
render();
announce("Quest map loaded");

// Offline after the first visit. Registration failing is not an error
// worth showing anyone - the site simply stays online-only.
if ("serviceWorker" in navigator && window.location.protocol.indexOf("http") === 0) {
  navigator.serviceWorker.register("sw.js").catch(function () {});
}
