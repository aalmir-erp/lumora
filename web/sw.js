/* Servia service worker — network-first for HTML/JS so deploys are seen instantly. */
const CACHE = "servia-v1.18.3";
const SHELL = [
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
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/pay/")) return;

  // Network-first for HTML / JS / CSS so new deploys are seen on next request.
  const isCode = /\.(html|js|css|json|webmanifest)$/i.test(url.pathname) ||
                 url.pathname === "/" || url.pathname.endsWith("/");
  if (isCode) {
    e.respondWith(
      fetch(e.request).then((res) => {
        if (e.request.method === "GET" && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      }).catch(() => caches.match(e.request).then(hit => hit || caches.match("/index.html")))
    );
    return;
  }

  // Cache-first for static images / icons.
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

// ---- Push notifications ----
self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : { title: "Servia", body: "You have a new update" };
  event.waitUntil(self.registration.showNotification(data.title || "Servia", {
    body: data.body || "",
    icon: "/icon-192.svg",
    badge: "/icon-192.svg",
    data: data.url || "/me.html",
    tag: data.tag || "servia-notif",
  }));
});
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data || "/me.html";
  event.waitUntil(clients.matchAll({type:"window"}).then(list => {
    for (const c of list) { if (c.url.includes(url) && "focus" in c) return c.focus(); }
    if (clients.openWindow) return clients.openWindow(url);
  }));
});
