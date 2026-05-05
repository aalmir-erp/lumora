/* Servia conversion tracker.
 *
 * Single global helper that fires GA4 / GTM / Facebook Pixel / TikTok Pixel
 * events when one is configured. Safe no-op when no analytics is loaded.
 *
 * Usage:
 *   window.serviaTrack("call_now", { source: "service_page" });
 *
 * Auto-bound from this file (no per-page wiring needed):
 *   - tel:        clicks  -> "call_now"
 *   - mailto:     clicks  -> "email_click"
 *   - wa.me / api.whatsapp.com / /contact.html -> "whatsapp_click"
 *   - data-event="X"      -> X     (any element with this attr)
 *   - data-bundle="X" + onclick to serviaAddToBundle -> "add_to_bundle"
 *
 * Pages can opt-out for an element by adding data-no-track.
 */
(function () {
  if (window.__servia_conv) return;
  window.__servia_conv = true;

  function fire(name, params) {
    if (!name) return;
    var p = params || {};
    p.page_path = location.pathname + location.search;
    try {
      if (typeof window.gtag === "function") window.gtag("event", name, p);
    } catch (_) {}
    try {
      if (window.dataLayer && window.dataLayer.push) {
        window.dataLayer.push(Object.assign({ event: name }, p));
      }
    } catch (_) {}
    try {
      if (window.fbq) window.fbq("trackCustom", name, p);
    } catch (_) {}
    try {
      if (window.ttq) window.ttq.track(name, p);
    } catch (_) {}
  }
  window.serviaTrack = fire;

  // Click delegation — works for content injected after page load.
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (!t) return;
    // Walk up to nearest A or BUTTON (or any element with data-event)
    var el = t.closest ? t.closest("a, button, [data-event]") : null;
    if (!el || el.hasAttribute("data-no-track")) return;

    // Explicit data-event wins
    var evt = el.getAttribute("data-event");
    if (evt) {
      fire(evt, { label: (el.getAttribute("data-event-label") || el.textContent || "").trim().slice(0, 80) });
      return;
    }

    // Implicit triggers
    var href = (el.getAttribute && el.getAttribute("href")) || "";
    if (href.indexOf("tel:") === 0) {
      fire("call_now", { number: href.slice(4) });
      return;
    }
    if (href.indexOf("mailto:") === 0) {
      fire("email_click", { to: href.slice(7).split("?")[0] });
      return;
    }
    if (
      href.indexOf("wa.me/") !== -1 ||
      href.indexOf("api.whatsapp.com") !== -1 ||
      href.indexOf("/contact.html") !== -1
    ) {
      fire("whatsapp_click", { dest: href });
      return;
    }
    // "+ Bundle" buttons — both <button data-bundle="X"> and inline serviaAddToBundle calls
    if (el.hasAttribute && el.hasAttribute("data-bundle")) {
      fire("add_to_bundle", { service_id: el.getAttribute("data-bundle") });
      return;
    }
    // Quote-request CTAs — any element labelled with a quote intent
    var label = (el.textContent || "").toLowerCase();
    if (
      el.id === "cta-book" ||
      el.id === "co-btn" ||
      label.indexOf("get instant quote") !== -1 ||
      label.indexOf("request quote") !== -1
    ) {
      fire("request_quote", { label: label.trim().slice(0, 60) });
      return;
    }
    // Share toolbar (rendered by share.js — has data-share or .servia-share-btn)
    if (
      (el.classList && el.classList.contains("servia-share-btn")) ||
      el.hasAttribute("data-share-platform")
    ) {
      fire("share_clicked", {
        platform: el.getAttribute("data-share-platform") || "",
        key: el.getAttribute("data-share-key") || "",
      });
      return;
    }
  }, { passive: true });

  // Page-load: fire context-specific conversions where the URL itself signals intent.
  // These let admins set up GA4 "key events" without per-page edits.
  function pageLoadEvents() {
    var p = location.pathname;
    var s = location.search || "";
    if (p === "/booked.html" || p.indexOf("/booked.html") === 0) {
      fire("book_service", { paid: s.indexOf("paid=1") !== -1 ? 1 : 0 });
      if (s.indexOf("paid=1") !== -1) fire("payment_completed", {});
    } else if (p === "/service.html") {
      var m = s.match(/[?&]id=([^&]+)/);
      fire("view_service_details", { service_id: m ? decodeURIComponent(m[1]) : "" });
    } else if (p.indexOf("/blog/") === 0) {
      fire("view_blog_post", { slug: p.slice(6) });
    } else if (p === "/cart.html") {
      fire("start_checkout", {});
    } else if (p.indexOf("/pay/") === 0) {
      fire("payment_started", { invoice: p.slice(5) });
    } else if (p.indexOf("/api/videos/play/") === 0) {
      fire("view_video", { slug: p.slice(17) });
    }
  }
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(pageLoadEvents, 0);
  } else {
    document.addEventListener("DOMContentLoaded", pageLoadEvents);
  }
})();
