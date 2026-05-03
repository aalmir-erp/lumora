/* Servia in-place CMS.
 *
 * Applies admin-saved per-element overrides on every page load by mapping
 * `data-cms-key="some.key"` attributes to text in the cms_overrides config.
 *
 * When an admin opens any page with `?edit=1` AND has a valid admin token in
 * localStorage, every [data-cms-key] element becomes contenteditable and a
 * floating bar appears with Save / Discard / Exit buttons.
 */
(function () {
  const KEY_TOK = "lumora.admin.tok";

  // 1) Apply overrides to every [data-cms-key] element on every page load.
  fetch("/api/admin/cms").then(r => r.ok ? r.json() : {}).then(map => {
    if (!map || typeof map !== "object") return;
    document.querySelectorAll("[data-cms-key]").forEach(el => {
      const k = el.dataset.cmsKey;
      if (k && map[k] != null) el.innerHTML = map[k];
    });
  }).catch(() => {});

  // 2) Edit mode toggled by ?edit=1 plus an admin token in localStorage.
  const params = new URLSearchParams(location.search);
  const editMode = params.get("edit") === "1";
  const adminTok = localStorage.getItem(KEY_TOK);
  if (!editMode || !adminTok) return;

  // Floating editor bar
  const bar = document.createElement("div");
  bar.style.cssText =
    "position:fixed;top:0;left:0;right:0;z-index:99999;background:linear-gradient(90deg,#7C3AED,#0F766E);" +
    "color:#fff;padding:10px 16px;display:flex;gap:10px;align-items:center;font-size:13px;font-weight:600;" +
    "box-shadow:0 4px 14px rgba(0,0,0,.18)";
  bar.innerHTML =
    '<span>✏ CMS edit mode — click any highlighted block to edit, then ' +
    '<button id="cms-save-all" style="background:#fff;color:#0F766E;border:0;padding:6px 14px;border-radius:999px;font-weight:700;cursor:pointer;font-size:12px">Save all</button> ' +
    '<button id="cms-exit" style="background:transparent;color:#fff;border:1px solid rgba(255,255,255,.5);padding:6px 14px;border-radius:999px;font-weight:700;cursor:pointer;font-size:12px;margin-inline-start:6px">Exit</button>' +
    '<span id="cms-count" style="margin-inline-start:auto;opacity:.85"></span>';
  document.body.insertBefore(bar, document.body.firstChild);
  document.body.style.paddingTop = "44px";

  // Highlight + make editable every cms element
  const dirty = new Set();
  const original = new Map();
  const els = document.querySelectorAll("[data-cms-key]");
  els.forEach(el => {
    el.contentEditable = "true";
    el.style.outline = "2px dashed rgba(124,58,237,.4)";
    el.style.outlineOffset = "2px";
    el.style.cursor = "text";
    original.set(el.dataset.cmsKey, el.innerHTML);
    el.addEventListener("input", () => {
      dirty.add(el.dataset.cmsKey);
      document.getElementById("cms-count").textContent = dirty.size + " unsaved";
    });
  });
  document.getElementById("cms-count").textContent = els.length + " editable blocks";

  document.getElementById("cms-save-all").onclick = async () => {
    if (!dirty.size) { alert("Nothing changed."); return; }
    let ok = 0, fail = 0;
    for (const key of dirty) {
      const el = document.querySelector(`[data-cms-key="${key}"]`);
      if (!el) continue;
      try {
        const r = await fetch("/api/admin/cms", {
          method: "POST",
          headers: { "content-type": "application/json", authorization: "Bearer " + adminTok },
          body: JSON.stringify({ key, html: el.innerHTML, page: location.pathname })
        });
        if (r.ok) ok++; else fail++;
      } catch { fail++; }
    }
    alert(`Saved ${ok}, failed ${fail}`);
    if (ok) dirty.clear();
    document.getElementById("cms-count").textContent = dirty.size + " unsaved";
  };

  document.getElementById("cms-exit").onclick = () => {
    if (dirty.size && !confirm("Discard unsaved changes?")) return;
    location.href = location.pathname;
  };
})();
