// App shell is cache-first. The timetable is network-first so new times show straight away,
// falling back to the saved copy when there is no signal (or the network takes over 4 s).
const CACHE = "omi-buses-v4";
const SHELL = ["./", "index.html", "manifest.webmanifest", "data/timetable.json", "icons/icon-180.png", "icons/icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.endsWith("/data/timetable.json")) {
    e.respondWith(caches.open(CACHE).then(async (c) => {
      const fresh = fetch(e.request, { cache: "no-cache" }).then((r) => {
        if (r.ok) c.put(e.request, r.clone());
        return r;
      });
      const slow = new Promise((res) => setTimeout(res, 4000));
      try {
        const r = await Promise.race([fresh, slow.then(() => c.match(e.request))]);
        if (r) return r;
      } catch (err) { /* offline: use the saved copy below */ }
      return (await c.match(e.request)) || fresh;
    }));
    return;
  }
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});
