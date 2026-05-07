/* Servia universal chrome injector. v1.24.32
 *
 * Earlier this file swapped nav.innerHTML / footer.innerHTML on
 * DOMContentLoaded and caused a visible layout shift. That approach is gone.
 *
 * What it does now is conservative and additive only — it injects pieces of
 * chrome that were inconsistently present across pages, without touching any
 * existing markup:
 *
 *   1. /widget.js (the Servia chat FAB) — loaded on every customer page.
 *      Audit found 17 of 30 pages were missing it, so the chat bubble was
 *      randomly absent.
 *
 *   2. A tiny WhatsApp companion FAB just above the chat bubble. Direct
 *      tap-to-WA handoff for users who'd rather skip the AI chat.
 *
 * Skip list: admin, vendor, portal, pay, invoice, login, sos, gate, reset,
 * brand-preview, 404 — pages that intentionally have bespoke chrome or
 * are not customer-facing.
 *
 * Body opt-out: pages can set <body data-chrome="off"> to disable injection
 * entirely.
 *
 * Layout-shift safety: nothing this script injects affects document flow.
 * widget.js mounts a position:fixed launcher; the WA FAB is also fixed.
 */
(function () {
  if (window.__servia_universal_nav) return;
  window.__servia_universal_nav = true;

  if (document.body && document.body.getAttribute("data-chrome") === "off") return;

  var SKIP = /^\/(admin|vendor|portal|pay|invoice|login|sos\.html|gate|reset|brand-preview|404|admin-login|admin-widget)/;
  if (SKIP.test(location.pathname)) return;

  // ---- 1. widget.js (chat FAB) -------------------------------------
  function ensureWidget() {
    if (document.querySelector('script[src="/widget.js"]')) return;
    var s = document.createElement("script");
    s.src = "/widget.js";
    s.defer = true;
    s.dataset.injected = "universal-nav";
    document.head.appendChild(s);
  }

  // ---- 2. Small WhatsApp companion FAB -----------------------------
  // Sits above the chat launcher (which lives at bottom-right).
  var WA_NUMBER = (window.SERVIA_WA || "971566900255").replace(/\D/g, "");
  function ensureWaFab() {
    if (document.getElementById("servia-wa-fab")) return;
    var a = document.createElement("a");
    a.id = "servia-wa-fab";
    a.href = "https://wa.me/" + WA_NUMBER + "?text=" +
             encodeURIComponent("Hi Servia, I need help.");
    a.target = "_blank";
    a.rel = "noopener";
    a.setAttribute("aria-label", "Chat on WhatsApp");
    a.title = "WhatsApp Servia";
    a.innerHTML = "💬";
    a.style.cssText = [
      "position:fixed",
      "right:18px",
      "bottom:142px",
      "width:48px",
      "height:48px",
      "border-radius:50%",
      "background:#075E54",
      "color:#fff",
      "display:flex",
      "align-items:center",
      "justify-content:center",
      "font-size:22px",
      "text-decoration:none",
      "box-shadow:0 6px 18px rgba(7,94,84,.45)",
      "z-index:998",
      "transition:transform .15s",
    ].join(";");
    a.addEventListener("mouseenter", function () {
      a.style.transform = "scale(1.08)";
    });
    a.addEventListener("mouseleave", function () {
      a.style.transform = "scale(1)";
    });
    document.body.appendChild(a);
  }

  function init() {
    ensureWidget();
    ensureWaFab();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
