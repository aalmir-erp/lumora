/* Servia floating "🛒 Bundle (n)" badge — visible on every page when the
 * cart has 1+ items. Tap → /cart.html. Defers init to idle.
 */
(function () {
  if (window.__servia_cart_badge) return; window.__servia_cart_badge = true;
  function init() {
    const KEY = "servia.cart.v1";
    function read() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (_) { return []; } }
    function refresh() {
      const n = read().length;
      let el = document.getElementById("servia-cart-badge");
      if (n === 0) { if (el) el.remove(); return; }
      if (!el) {
        el = document.createElement("a");
        el.id = "servia-cart-badge";
        el.href = "/cart.html";
        el.style.cssText =
          "position:fixed;left:14px;bottom:78px;z-index:998;" +
          "background:linear-gradient(135deg,#0F766E,#F59E0B);color:#fff;" +
          "border-radius:999px;padding:11px 18px;font-weight:800;font-size:14px;" +
          "box-shadow:0 8px 22px rgba(15,23,42,.22);text-decoration:none;" +
          "display:inline-flex;align-items:center;gap:8px;line-height:1;" +
          "transition:transform .12s";
        el.onmouseover = () => el.style.transform = "translateY(-2px)";
        el.onmouseout = () => el.style.transform = "";
        document.body.appendChild(el);
      }
      el.innerHTML = '🛒 <span>Bundle (' + n + ')</span>';
    }
    refresh();
    window.addEventListener("storage", e => { if (e.key === KEY) refresh(); });
    // Re-check periodically (simple, no external lib)
    setInterval(refresh, 3000);
    // Public helper that other scripts can call to add a service to cart
    window.serviaAddToBundle = function (item) {
      const cur = read();
      cur.push({...item, _ts: Date.now()});
      localStorage.setItem(KEY, JSON.stringify(cur));
      refresh();
      // Brief toast
      const t = document.createElement("div");
      t.textContent = "✓ Added to bundle (" + cur.length + ") — open cart →";
      t.style.cssText = "position:fixed;left:50%;top:24px;transform:translateX(-50%);" +
        "background:#065F46;color:#fff;padding:10px 18px;border-radius:999px;z-index:99999;" +
        "font-size:13.5px;font-weight:700;box-shadow:0 8px 22px rgba(15,23,42,.22);";
      t.onclick = () => location.href = "/cart.html";
      document.body.appendChild(t);
      setTimeout(() => t.remove(), 3000);
    };
  }
  if ("requestIdleCallback" in window) requestIdleCallback(init, { timeout: 3000 });
  else setTimeout(init, 1500);
})();
