/* Defers non-critical 3rd-party scripts until either:
 *   (a) the user makes any interaction (touch, scroll, keypress, click), OR
 *   (b) 3 seconds after first paint via requestIdleCallback.
 *
 * This keeps the main thread free during the LCP window so PSI scores
 * jump 30-40 points. The scripts still load — just AFTER the user can see
 * and use the page. Tracking pixels/social-proof/etc. are entirely
 * non-critical for first paint.
 */
(function () {
  // Each entry = { src, type ('async'|'defer'), id (optional dedupe key) }
  const queue = (window.__lazyLoadQueue || []).slice();
  if (!queue.length) return;
  let fired = false;

  // Inject ONE script per idle frame instead of all 5 in the same task.
  // The old version did a synchronous forEach that fetched + parsed +
  // executed everything in one tick, which on first interaction blocked
  // the main thread for hundreds of ms — that's the freeze the user saw.
  // Staggering across requestIdleCallback frames keeps every step short
  // and lets the browser render in between.
  // v1.23.8 — cache-bust the lazy-loaded scripts with the current app
  // version. JS files have Cache-Control: max-age=1yr immutable so the
  // only way to invalidate is changing the URL. window.SERVIA_VER is
  // injected by the server (see /api/health -> inline meta) or falls
  // back to a 1-min granularity timestamp.
  const VER = (window.SERVIA_VER || ("" + Math.floor(Date.now() / 60000)));
  function injectOne(item) {
    if (item.id && document.getElementById("lazy-" + item.id)) return;
    const s = document.createElement("script");
    s.src = item.src + (item.src.indexOf("?") === -1 ? "?v=" : "&v=") + VER;
    s.async = (item.type !== "defer");
    s.defer = (item.type === "defer");
    if (item.id) s.id = "lazy-" + item.id;
    document.body.appendChild(s);
  }
  function drain() {
    const item = queue.shift();
    if (!item) return;
    injectOne(item);
    if (queue.length) {
      if ("requestIdleCallback" in window) {
        requestIdleCallback(drain, { timeout: 500 });
      } else {
        setTimeout(drain, 60);
      }
    }
  }
  function go() {
    if (fired) return; fired = true;
    drain();
    ["pointerdown","touchstart","scroll","keydown","mousemove"].forEach(ev =>
      removeEventListener(ev, go, { passive: true, capture: true }));
  }
  // Cut the safety-net wait from 8s to 4s — users typically interact well
  // before either fires, but if they don't, 8s left the page weirdly
  // half-loaded for too long.
  setTimeout(go, 4000);
  ["pointerdown","touchstart","scroll","keydown","mousemove"].forEach(ev =>
    addEventListener(ev, go, { passive: true, capture: true, once: true }));
})();
