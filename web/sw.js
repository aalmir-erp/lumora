/* Lumora service worker — minimal offline shell + asset cache. */
const CACHE = "lumora-v0.2.0";
const SHELL = [
  "/", "/index.html", "/services.html", "/book.html", "/account.html",
  "/style.css", "/app.js", "/widget.js", "/widget.css", "/i18n.js",
  "/logo.svg", "/avatar.svg", "/icon-192.svg", "/icon-512.svg",
  "/manifest.webmanifest"
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // Never cache API or admin/portal traffic.
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/pay/")) return;
  e.respondWith(
    caches.match(e.request).then((hit) =>
      hit ||
      fetch(e.request).then((res) => {
        if (e.request.method === "GET" && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => caches.match("/index.html"))
    )
  );
});
