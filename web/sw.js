/* Servia service worker — network-first for HTML/JS so deploys are seen instantly. */
const CACHE = "servia-v1.24.213";
// v1.23.0 — pre-cache critical paint-path assets so first visit is instant
// on a returning user. Keep small (<200KB total) to not blow Android cache.
const SHELL = [
  "/", "/index.html",
  "/logo.svg", "/avatar.svg", "/icon-192.svg", "/icon-512.svg",
  "/style.css", "/widget.css",
  "/manifest.webmanifest",
  "/mascot.svg",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  // v1.24.20 — aggressive cache wipe AND ask all open clients to reload
  // so they don't keep running stale broken JS. Customer reported a
  // blank-white-screen state on servia.ae caused by v1.24.18's broken
  // minify middleware corrupting cached JS. This activate handler now
  // clears EVERY non-current cache + force-reloads any open tabs after
  // taking control.
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
    await self.clients.claim();
    const all = await self.clients.matchAll({type: "window"});
    for (const c of all) {
      try { c.postMessage({type: "sw-updated", cache: CACHE}); } catch (_) {}
    }
  })());
});

// Allow the page to ask us to wipe + skipWaiting on demand (used by
// the ?reset URL handler).
self.addEventListener("message", (e) => {
  if (!e.data || e.data.type !== "servia-reset") return;
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map((k) => caches.delete(k)));
    self.skipWaiting();
    const all = await self.clients.matchAll({type: "window"});
    for (const c of all) c.navigate(c.url.split("?")[0]);
  })());
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // v1.24.20 — emergency reset hatch. If URL has ?reset / ?clear-sw,
  // bypass cache entirely so the user can force-fetch the latest HTML.
  if (url.search.includes("reset") || url.search.includes("clear-sw") ||
      url.search.includes("nocache")) return;
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/pay/")) return;

  // Network-first for HTML / JS / CSS so new deploys are seen on next request.
  // v1.24.200 — Force the SW's fetch to bypass the browser's HTTP cache too
  // (`cache: "no-store"`). Without this, an older Cache-Control directive
  // from a previous deploy (e.g. stale-while-revalidate=86400) could keep
  // returning stale HTML for up to 24h even though the SW is asking for it
  // from "the network". Founder hit this: v1.24.196/197/199 fixes were live
  // on servia.ae but the TWA + mobile Chrome kept serving stale HTML.
  const isCode = /\.(html|js|css|json|webmanifest)$/i.test(url.pathname) ||
                 url.pathname === "/" || url.pathname.endsWith("/");
  if (isCode) {
    const noStoreReq = new Request(e.request, { cache: "no-store" });
    e.respondWith(
      fetch(noStoreReq).then((res) => {
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
  // v1.24.213 — delivery id (assigned server-side) ping back on click for
  // open-rate tracking. Stashed in notification.data.did.
  const did = data._did || null;

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

  // Body emoji + actions per category. v1.24.213 — payload.actions
  // (from admin broadcast composer) overrides the category defaults so
  // operators can supply custom CTA buttons with their own URLs.
  let actions = [];
  if (Array.isArray(data.actions) && data.actions.length) {
    actions = data.actions.slice(0, 2).map(a => ({
      action: String(a.action || "open").slice(0, 30),
      title:  String(a.title  || "Open").slice(0, 30),
      icon:   "/icon-192.png",
    }));
  } else if (kind === "new_visitor") {
    actions = [{ action: "view-live", title: "View live", icon: "/icon-192.png" }];
  } else if (kind === "new_booking" || kind === "booking_confirmed") {
    actions = [{ action: "view-booking", title: "Open booking", icon: "/icon-192.png" }];
  } else if (kind === "payment_request") {
    actions = [{ action: "send-link", title: "Send WA link", icon: "/icon-192.png" }];
  }

  // v1.24.213 — Default tap URL: customer notifications open the app
  // homepage (so the chat / quick-book is one tap away); admin-flavoured
  // pushes (new_visitor, new_booking, payment_request) go to admin tab.
  const adminKinds = new Set([
    "new_visitor", "new_booking", "booking_confirmed",
    "payment_request", "psi_alert", "test"
  ]);
  const defaultUrl = adminKinds.has(kind)
    ? "/admin.html#" + (kind === "new_visitor" ? "live" : "dashboard")
    : "/";
  event.waitUntil(self.registration.showNotification(data.title || "Servia", {
    body: data.body || "",
    icon: "/icon-192.png",        // colour app icon (large)
    badge: "/badge-72.png",       // monochrome silhouette for status bar
    image: data.image,
    data: {
      url: data.url || defaultUrl,
      did: did,
      // Per-action URL map: { "<action_id>": "<url>" } so the
      // notificationclick handler can look up where an action button
      // should take the user.
      actionUrls: (Array.isArray(data.actions) ? data.actions : [])
        .reduce((o, a) => { if (a.action && a.url) o[a.action] = a.url; return o; }, {}),
    },
    tag: data.tag || ("servia-" + kind || "servia-notif"),
    renotify: true,
    requireInteraction: kind === "payment_request" || kind === "psi_alert",
    silent: false,
    vibrate,
    actions,
  }));
});
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  // v1.24.213 — `data` is now an object {url, did, actionUrls}. Old
  // notifications (already on phones) may still have data as a raw URL
  // string; handle both for back-compat.
  let target, did = null, actionUrls = {};
  const d = event.notification.data;
  if (d && typeof d === "object") {
    target = d.url || "/";
    did = d.did || null;
    actionUrls = d.actionUrls || {};
  } else {
    target = (typeof d === "string" && d) ? d : "/";
  }
  // If a specific action button was tapped, prefer its URL; otherwise the
  // notification body itself (event.action is "" for the body click).
  if (event.action && actionUrls[event.action]) {
    target = actionUrls[event.action];
  }
  event.waitUntil((async () => {
    // 1. Fire-and-forget click ping for open-rate tracking.
    if (did) {
      try { await fetch("/api/push/click/" + did, {method:"POST", keepalive:true}); }
      catch (_) {}
    }
    // 2. Reuse an existing app window if one's already open.
    const list = await clients.matchAll({type:"window", includeUncontrolled:true});
    for (const c of list) {
      if (c.url.endsWith(target) && "focus" in c) { try { return c.focus(); } catch(_){} }
    }
    // 3. Otherwise open the target. Browser/TWA auto-picks the right
    //    handler — if the TWA app is installed and the URL is on our
    //    domain, Android opens the TWA full-screen; else default browser.
    if (clients.openWindow) {
      const abs = (target.startsWith("http") || target.startsWith("/"))
        ? target : ("/" + target);
      return clients.openWindow(abs);
    }
  })());
});
