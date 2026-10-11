// The page and the timetable are network-first so changes show straight away, falling back
// to the saved copy when there is no signal (or the network takes over 4 s).
// Icons and the manifest are cache-first. Bump VERSION (and APP_VERSION in index.html) on every release.
const VERSION = 8;
const CACHE = `omi-buses-v${VERSION}`;
const SHELL = ["./", "index.html", "manifest.webmanifest", "data/timetable.json", "icons/icon-180.png", "icons/icon-192.png"];

self.addEventListener("install", (e) => {
  // cache: "reload" skips the phone's HTTP cache, so an update never stores stale copies.
  e.waitUntil(caches.open(CACHE)
    .then((c) => c.addAll(SHELL.map((u) => new Request(u, { cache: "reload" }))))
    .then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

async function networkFirst(request, key) {
  const c = await caches.open(CACHE);
  const fresh = fetch(request, { cache: "no-cache" }).then((r) => {
    if (r.ok) c.put(key, r.clone());
    return r;
  });
  const slow = new Promise((res) => setTimeout(res, 4000));
  try {
    const r = await Promise.race([fresh, slow.then(() => c.match(key))]);
    if (r) return r;
  } catch (err) { /* offline: use the saved copy below */ }
  return (await c.match(key)) || fresh;
}

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (e.request.mode === "navigate" || url.pathname.endsWith("/index.html")) {
    e.respondWith(networkFirst(e.request, "./"));
    return;
  }
  if (url.pathname.endsWith("/data/timetable.json")) {
    e.respondWith(networkFirst(e.request, "data/timetable.json"));
    return;
  }
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
