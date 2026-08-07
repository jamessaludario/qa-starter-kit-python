/* Service worker: makes the site work offline after the first visit.
 *
 * Two strategies, and the split matters:
 *
 *   the PAGE itself  -> network first, cache as a fallback
 *   everything else  -> cache first
 *
 * Cache-first is right for the assets: the biggest by far is an 11 MB
 * Python runtime, it is immutable for a given build, and a learner on a
 * train should not lose their lesson to a dropped connection. Every one
 * of those URLs carries a ?v=<build id>, so a new build asks for new
 * URLs and can never be served an old file.
 *
 * But index.html is the document that PINS those versions - it is where
 * the ?v= comes from. Caching it first means a rebuilt site keeps
 * loading the old page, which keeps requesting the old assets, and the
 * learner never sees the new content no matter how many times they
 * reload. It is a few hundred bytes, so fetching it fresh costs nothing
 * and the cached copy is still there when the network is gone.
 *
 * The cache name carries the build id, so activating a new build drops
 * the old cache wholesale rather than serving half-old, half-new files.
 */

var CACHE = "quest-e38f1aa4a5";

// The app shell, injected by build_site.py. NOT the 11 MB Python
// runtime: that is fetched only when a coding challenge needs it, and
// precaching it here would undo the whole lazy-loading story.
var SHELL = ["./", "app.css?v=e38f1aa4a5", "content.js?v=e38f1aa4a5", "pylib.js?v=e38f1aa4a5", "js/main.js?v=e38f1aa4a5", "fonts/fonts.css", "fonts/IBMPlexMono-400.woff2", "fonts/IBMPlexMono-600.woff2", "fonts/IBMPlexSans-400.woff2", "fonts/IBMPlexSerif-400.woff2", "fonts/IBMPlexSerif-600.woff2", "js/bridge.js", "js/dom.js", "js/editor.js", "js/game.js", "js/grade.js", "js/runner.js", "js/selector-engine.js", "js/store.js", "js/views/challenge.js", "js/views/map.js", "js/views/terrain.js", "js/views/victory.js", "js/views/zone.js", "mockapp/app.js", "mockapp/index.html", "mockapp/style.css"];

self.addEventListener("install", function (event) {
  // Fill the cache at INSTALL time, not on the first intercepted
  // request. On a first visit the worker is not controlling the page
  // yet, so nothing that load fetched passes through the fetch handler
  // - without this, "works offline after the first visit" is simply
  // untrue, and the learner who closes the lid on the train gets a
  // blank page.
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      // One at a time with a catch, rather than cache.addAll(), which
      // rejects the whole install if a single file 404s. A shell that
      // is one file short still beats no shell at all.
      return Promise.all(SHELL.map(function (url) {
        return cache.add(url).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (names) {
        return Promise.all(names.filter(function (name) {
          return name !== CACHE;
        }).map(function (name) { return caches.delete(name); }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

function keep(cache, request, response) {
  // Only cache real successes: a cached 404 is a bug that survives a
  // reload.
  if (response.ok && response.type === "basic") {
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", function (event) {
  if (event.request.method !== "GET") return;
  var url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  // A navigation is the browser asking for the page itself.
  var isPage = event.request.mode === "navigate";

  event.respondWith(
    caches.open(CACHE).then(function (cache) {
      if (isPage) {
        return fetch(event.request)
          .then(function (response) { return keep(cache, event.request, response); })
          .catch(function () {
            // Offline. Fall back to the cached page, and to the site
            // root for a deep link we have never served before - the
            // routing is hash-based, so index.html can render any of it.
            return cache.match(event.request)
              .then(function (hit) { return hit || cache.match("./"); });
          });
      }
      return cache.match(event.request).then(function (hit) {
        if (hit) return hit;
        return fetch(event.request).then(function (response) {
          return keep(cache, event.request, response);
        });
      });
    })
  );
});
