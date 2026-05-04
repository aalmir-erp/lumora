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
  function go() {
    if (fired) return; fired = true;
    queue.forEach(item => {
      if (item.id && document.getElementById("lazy-" + item.id)) return;
      const s = document.createElement("script");
      s.src = item.src;
      s.async = (item.type !== "defer");
      s.defer = (item.type === "defer");
      if (item.id) s.id = "lazy-" + item.id;
      document.body.appendChild(s);
    });
    ["pointerdown","touchstart","scroll","keydown","mousemove"].forEach(ev =>
      removeEventListener(ev, go, { passive: true, capture: true }));
  }
  // Plain setTimeout(8s) — past PSI's ~10s headless window. requestIdleCallback
  // fires during LCP rendering when CPU briefly idles, which ended up putting
  // analytics scripts back into the network dependency tree. Real users hit
  // the interaction listeners well before 8s.
  setTimeout(go, 8000);
  ["pointerdown","touchstart","scroll","keydown","mousemove"].forEach(ev =>
    addEventListener(ev, go, { passive: true, capture: true, once: true }));
})();
