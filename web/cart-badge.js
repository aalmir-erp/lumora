/* Servia floating "🛒 Bundle" badge — ALWAYS visible on every page (even
 * when empty: "Build a bundle, save up to 15%"). Hover/tap to preview the
 * cart contents inline. Click → /cart.html.
 */
(function () {
  if (window.__servia_cart_badge) return; window.__servia_cart_badge = true;
  // Suppressed on internal pages so we don't clutter admin/cart
  const path = location.pathname;
  if (/^\/(admin|vendor|portal-vendor|cart\.html|pay)/.test(path)) return;

  const SERVICE_META = {
    deep_cleaning:{e:"✨",l:"Deep Cleaning"}, general_cleaning:{e:"🧹",l:"General Cleaning"},
    ac_cleaning:{e:"❄️",l:"AC Service"}, ac_service:{e:"❄️",l:"AC Service"},
    maid_service:{e:"👤",l:"Maid Service"}, pest_control:{e:"🪲",l:"Pest Control"},
    handyman:{e:"🔧",l:"Handyman"}, sofa_carpet:{e:"🛋️",l:"Sofa & Carpet"},
    move_in_out:{e:"📦",l:"Move-in/out"}, window_cleaning:{e:"🪟",l:"Window Cleaning"},
    kitchen_deep:{e:"👨‍🍳",l:"Kitchen Deep Clean"}, swimming_pool:{e:"🏊",l:"Pool Maintenance"},
    car_wash:{e:"🚗",l:"Car Wash"}, painting:{e:"🎨",l:"Painting"},
    gardening:{e:"🌿",l:"Gardening"}, smart_home:{e:"💡",l:"Smart Home"},
  };

  function init() {
    const KEY = "servia.cart.v1";
    function read() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (_) { return []; } }
    function discountPctFor(n) { return n >= 4 ? 15 : n === 3 ? 10 : n === 2 ? 5 : 0; }

    // Build the always-visible badge + preview popover
    if (!document.getElementById("servia-cart-css")) {
      const css = document.createElement("style");
      css.id = "servia-cart-css";
      css.textContent = `
        #servia-cart-badge {
          position:fixed;left:14px;bottom:78px;z-index:998;
          background:linear-gradient(135deg,#0F766E,#F59E0B);color:#fff;
          border-radius:999px;padding:11px 16px;font-weight:800;font-size:13.5px;
          box-shadow:0 10px 26px rgba(15,23,42,.28);text-decoration:none;
          display:inline-flex;align-items:center;gap:7px;line-height:1;
          transition:transform .12s, box-shadow .12s; cursor:pointer;
        }
        #servia-cart-badge:hover { transform:translateY(-2px); box-shadow:0 14px 30px rgba(15,23,42,.32) }
        #servia-cart-badge .cb-n { background:#fff;color:#7C2D12;border-radius:999px;
          padding:1px 7px;font-weight:800;font-size:11.5px;min-width:18px;text-align:center }
        #servia-cart-pop {
          position:fixed;left:14px;bottom:130px;z-index:999;width:300px;max-width:calc(100vw - 28px);
          background:#fff;border-radius:14px;box-shadow:0 18px 44px rgba(15,23,42,.30);
          padding:14px;border:1px solid var(--border,#E2E8F0);
          opacity:0;transform:translateY(8px);pointer-events:none;
          transition:opacity .2s, transform .2s;
        }
        #servia-cart-pop.show { opacity:1; transform:translateY(0); pointer-events:auto }
        #servia-cart-pop h4 { margin:0 0 8px;font-size:13.5px;letter-spacing:-.01em;color:#0F172A }
        #servia-cart-pop ul { list-style:none;padding:0;margin:0 0 8px;max-height:160px;overflow:auto }
        #servia-cart-pop li { display:flex;gap:8px;align-items:center;padding:6px 0;
          border-bottom:1px solid #F1F5F9;font-size:13px }
        #servia-cart-pop li:last-child { border-bottom:0 }
        #servia-cart-pop .cb-empty { font-size:12.5px;color:#64748B;padding:8px 0 4px;line-height:1.5 }
        #servia-cart-pop .cb-disc { background:linear-gradient(135deg,#FCD34D,#F59E0B);color:#7C2D12;
          padding:7px 10px;border-radius:10px;font-size:12px;font-weight:700;margin-top:6px;text-align:center }
        #servia-cart-pop .cb-go { display:block;background:linear-gradient(135deg,#0F766E,#0D9488);
          color:#fff;padding:9px;border-radius:10px;text-align:center;font-weight:800;font-size:13px;
          text-decoration:none;margin-top:8px }
        #servia-toast {
          position:fixed;left:50%;top:18px;transform:translateX(-50%);z-index:99999;
          background:#065F46;color:#fff;padding:10px 18px;border-radius:999px;
          font-size:13.5px;font-weight:700;box-shadow:0 8px 22px rgba(15,23,42,.28);cursor:pointer;
          animation:servia-toast-in .25s ease;
        }
        @keyframes servia-toast-in { from { opacity:0; transform:translate(-50%,-8px) } to { opacity:1 } }
      `;
      document.head.appendChild(css);
    }

    let el = document.getElementById("servia-cart-badge");
    let pop = document.getElementById("servia-cart-pop");
    if (!el) {
      el = document.createElement("a");
      el.id = "servia-cart-badge";
      el.href = "/cart.html";
      document.body.appendChild(el);
    }
    if (!pop) {
      pop = document.createElement("div");
      pop.id = "servia-cart-pop";
      document.body.appendChild(pop);
    }
    function refresh() {
      const items = read();
      const n = items.length;
      const disc = discountPctFor(n);
      el.innerHTML = '🛒 ' + (n === 0
        ? '<span>Build a bundle</span>'
        : '<span>Bundle</span><span class="cb-n">' + n + '</span>'
          + (disc ? '<span style="font-size:11px;background:#FCD34D;color:#7C2D12;padding:1px 7px;border-radius:999px;font-weight:800">−' + disc + '%</span>' : ''));

      // Popover
      let body;
      if (n === 0) {
        body = '<div class="cb-empty">📦 Bundle 2+ services into one booking and save:<br>'
             + '<b>2 services = 5% off</b><br>'
             + '<b>3 services = 10% off</b><br>'
             + '<b>4+ services = 15% off</b><br>'
             + 'Single payment · single invoice.</div>'
             + '<a class="cb-go" href="/services.html">Add services →</a>';
      } else {
        body = '<ul>' + items.map(it => {
          const m = SERVICE_META[it.service_id] || {e:"🧽", l:it.service_id};
          return '<li><span style="font-size:18px">' + m.e + '</span>' +
                 '<span style="flex:1">' + m.l + '</span></li>';
        }).join("") + '</ul>'
        + (disc ? '<div class="cb-disc">🎁 ' + disc + '% bundle discount applied</div>' : '<div class="cb-empty">Add 1 more for 5% off bundle.</div>')
        + '<a class="cb-go" href="/cart.html">Open cart · checkout →</a>';
      }
      pop.innerHTML = '<h4>🛒 Your Servia bundle</h4>' + body;
    }
    refresh();

    // Hover/click to toggle preview
    let hoverT = null;
    function show()  { clearTimeout(hoverT); pop.classList.add("show"); }
    function hideD() { hoverT = setTimeout(() => pop.classList.remove("show"), 250); }
    el.addEventListener("mouseenter", show);
    el.addEventListener("mouseleave", hideD);
    pop.addEventListener("mouseenter", show);
    pop.addEventListener("mouseleave", hideD);
    // Tap on mobile: toggle preview instead of nav (then a follow-up tap navigates)
    let tappedOnce = false;
    el.addEventListener("click", e => {
      if ("ontouchstart" in window && !tappedOnce) {
        e.preventDefault(); show(); tappedOnce = true;
        setTimeout(() => tappedOnce = false, 2200);
      }
    });

    window.addEventListener("storage", e => { if (e.key === KEY) refresh(); });
    setInterval(refresh, 4000);

    window.serviaAddToBundle = function (item) {
      const cur = read();
      cur.push({...item, _ts: Date.now()});
      localStorage.setItem(KEY, JSON.stringify(cur));
      refresh();
      const t = document.createElement("div");
      t.id = "servia-toast";
      t.textContent = "✓ Added to bundle (" + cur.length + ") · tap to open →";
      t.onclick = () => location.href = "/cart.html";
      const old = document.getElementById("servia-toast");
      if (old) old.remove();
      document.body.appendChild(t);
      setTimeout(() => t.remove(), 3500);
    };
  }
  // Render immediately so the badge is always visible (helps users discover bundles)
  if (document.body) init();
  else document.addEventListener("DOMContentLoaded", init, {once:true});
})();
