/* v1.24.55 — Servia Admin Live PWA service worker.

   Receives Web Push notifications from server and shows them with a
   "Reply" action. Wear OS / Apple Watch automatically mirror these
   notifications to the paired watch with quick-reply support.
   Tapping the notification opens admin-live.html with the chat focused.
*/
'use strict';

self.addEventListener("install", e => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));

self.addEventListener("push", event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) {}
  const kind = (data.kind || "").toLowerCase();
  const title = data.title || "Servia";
  const body  = data.body  || "";
  const sid   = data.session_id || data.sid || "";

  // Per-kind vibration for feel
  const VIBRATION = {
    new_visitor:       [80, 60, 80, 60, 80],
    new_booking:       [120, 80, 200, 80, 200, 80, 400],
    booking_confirmed: [200, 100, 400],
    payment_request:   [400, 200, 400],
    chat_message:      [60, 40, 60, 40, 60],
    urgent_handoff:    [200, 100, 200, 100, 600],
  };
  const vibrate = VIBRATION[kind] || [120, 80, 120];

  // Reply action makes the watch mirror with voice / quick-reply
  const actions = [];
  if (sid) {
    actions.push({
      action: "reply",
      title: "💬 Reply",
      type:  "text",
      placeholder: "Quick reply…",
    });
    actions.push({ action: "open", title: "📂 Open chat" });
  }

  event.waitUntil(self.registration.showNotification(title, {
    body,
    icon: "/icon-192.svg",
    badge: "/icon-192.svg",
    image: data.image,
    data: { sid, url: data.url || "/admin-live.html", kind },
    tag: data.tag || ("servia-admin-" + (sid || kind)),
    renotify: true,
    requireInteraction: kind === "urgent_handoff" || kind === "payment_request",
    silent: false,
    vibrate,
    actions,
  }));
});

self.addEventListener("notificationclick", event => {
  const action = event.action;
  const data = event.notification.data || {};
  event.notification.close();

  // Quick-reply from the notification (works on Wear OS + phone)
  if (action === "reply" && event.reply && data.sid) {
    const replyText = String(event.reply || "").trim();
    if (replyText) {
      event.waitUntil((async () => {
        // We don't have the admin token in the SW context, so we POST to
        // a SW-friendly endpoint that re-derives auth from a stored cookie
        // OR from the most recent admin-live.html session. For now, store
        // the token via an explicit message from the page.
        const tok = await getStoredToken();
        if (!tok) return openOrFocus("/admin-live.html?sid=" + encodeURIComponent(data.sid));
        await fetch("/api/admin/live/chat/" + encodeURIComponent(data.sid) + "/reply", {
          method: "POST",
          headers: { "Authorization": "Bearer " + tok, "Content-Type": "application/json" },
          body: JSON.stringify({ text: replyText }),
        }).catch(()=>{});
      })());
      return;
    }
  }

  // Default: open or focus the admin-live PWA at the right session
  const url = data.sid ? "/admin-live.html?sid=" + encodeURIComponent(data.sid) : (data.url || "/admin-live.html");
  event.waitUntil(openOrFocus(url));
});

async function openOrFocus(url) {
  const all = await clients.matchAll({ type: "window", includeUncontrolled: true });
  for (const c of all) {
    if (c.url.includes("/admin-live.html") && "focus" in c) {
      try { c.navigate(url); } catch (_) {}
      return c.focus();
    }
  }
  if (clients.openWindow) return clients.openWindow(url);
}

// Token bridge — admin-live.html posts its token to the SW so notification
// reply actions can use it.
self.addEventListener("message", e => {
  if (!e.data) return;
  if (e.data.type === "set-admin-token") {
    self._adminToken = e.data.token || "";
  }
});
async function getStoredToken() {
  if (self._adminToken) return self._adminToken;
  // Fallback: ask any open admin-live page
  const all = await clients.matchAll({ type: "window", includeUncontrolled: true });
  for (const c of all) {
    if (c.url.includes("/admin-live.html")) {
      const tok = await new Promise(resolve => {
        const ch = new MessageChannel();
        ch.port1.onmessage = ev => resolve(ev.data && ev.data.token);
        c.postMessage({ type: "get-admin-token" }, [ch.port2]);
        setTimeout(() => resolve(""), 500);
      });
      if (tok) { self._adminToken = tok; return tok; }
    }
  }
  return "";
}
