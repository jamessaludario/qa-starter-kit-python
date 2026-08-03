/* Service worker: makes the site work offline after the first visit.
 *
 * Cache-first, filled at runtime. That is the right strategy here
 * because the biggest asset by far - an 11 MB Python runtime - is
 * immutable for a given build, and a learner on a train should not lose
 * their lesson to a dropped connection.
 *
 * The cache name carries the build id, so a rebuilt site invalidates
 * everything at once instead of serving half-old, half-new files.
 */

var CACHE = "quest-__BUILD_ID__";

self.addEventListener("install", function () {
  self.skipWaiting();
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

self.addEventListener("fetch", function (event) {
  if (event.request.method !== "GET") return;
  var url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.open(CACHE).then(function (cache) {
      return cache.match(event.request).then(function (hit) {
        if (hit) return hit;
        return fetch(event.request).then(function (response) {
          // Only cache real successes: a cached 404 is a bug that
          // survives a reload.
          if (response.ok && response.type === "basic") {
            cache.put(event.request, response.clone());
          }
          return response;
        });
      });
    })
  );
});
