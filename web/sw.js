/* Servia service worker — network-first for HTML/JS so deploys are seen instantly. */
const CACHE = "servia-v1.22.65";
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
// Different categories get different vibration patterns + actions so admin
// can identify new-visitor pings vs bookings vs payment alerts at a glance.
self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : { title: "Servia", body: "You have a new update" };
  const kind = (data.kind || "").toLowerCase();

  // Vibration patterns: distinct fingerprint per category
  // (Android picks the OS sound; vibration is the most reliable cross-device signal)
  const VIBRATION = {
    new_visitor:       [80, 60, 80, 60, 80],            // 3 quick taps — "someone landed"
    new_booking:       [120, 80, 200, 80, 200, 80, 400], // crescendo — important
    booking_confirmed: [200, 100, 400],                  // 2 tones — payment cleared
    payment_request:   [400, 200, 400],                  // long pulses — needs action
    psi_alert:         [300, 100, 100, 100, 300],        // signal — warning
    article_published: [60, 40, 60],                      // soft — informational
    magic_link:        [100, 100, 100],                   // tap-tap-tap
  };
  const vibrate = VIBRATION[kind] || [200, 100, 200];

  // Body emoji + actions per category
  let actions = [];
  if (kind === "new_visitor") {
    actions = [{ action: "view-live", title: "👀 View live", icon: "/icon-192.svg" }];
  } else if (kind === "new_booking" || kind === "booking_confirmed") {
    actions = [{ action: "view-booking", title: "📋 Open booking", icon: "/icon-192.svg" }];
  } else if (kind === "payment_request") {
    actions = [{ action: "send-link", title: "💬 Send WA link", icon: "/icon-192.svg" }];
  }

  event.waitUntil(self.registration.showNotification(data.title || "Servia", {
    body: data.body || "",
    icon: "/icon-192.svg",
    badge: "/icon-192.svg",
    image: data.image,
    data: data.url || "/admin.html#" + (kind === "new_visitor" ? "live" : "dashboard"),
    tag: data.tag || ("servia-" + kind || "servia-notif"),
    renotify: true,            // re-vibrate even if same tag still showing
    requireInteraction: kind === "payment_request" || kind === "psi_alert",
    silent: false,
    vibrate,
    actions,
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
