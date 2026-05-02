/* Lumora theme + font picker. Stores choice in localStorage; applied via data-theme + data-font on <html>. */
(function () {
  const LS_THEME = "lumora.theme";
  const LS_FONT  = "lumora.font";

  const THEMES = {
    light:    { label: "☀️ Light",     primary:"#0D9488", primaryDark:"#115E59", accent:"#F59E0B",
                bg:"#F8FAFC", surface:"#FFFFFF", text:"#0F172A", muted:"#64748B", border:"#E2E8F0" },
    dark:     { label: "🌙 Dark",      primary:"#2DD4BF", primaryDark:"#14B8A6", accent:"#FBBF24",
                bg:"#0F172A", surface:"#1E293B", text:"#F1F5F9", muted:"#94A3B8", border:"#334155" },
    sand:     { label: "🌅 Sand",      primary:"#B45309", primaryDark:"#78350F", accent:"#0D9488",
                bg:"#FFFBEB", surface:"#FFFFFF", text:"#451A03", muted:"#92400E", border:"#FED7AA" },
    midnight: { label: "🌌 Midnight",  primary:"#A78BFA", primaryDark:"#7C3AED", accent:"#F472B6",
                bg:"#020617", surface:"#0F172A", text:"#F1F5F9", muted:"#94A3B8", border:"#1E293B" },
  };
  const FONTS = {
    "system":  { label: "System (Default)",
                 stack: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
    "inter":   { label: "Inter (Modern)",
                 stack: '"Inter","Segoe UI", Roboto, sans-serif',
                 google: "Inter:wght@400;500;600;700;800" },
    "dmsans":  { label: "DM Sans (Clean)",
                 stack: '"DM Sans","Segoe UI", sans-serif',
                 google: "DM+Sans:wght@400;500;700" },
    "playfair":{ label: "Playfair (Premium serif)",
                 stack: '"Playfair Display", Georgia, serif',
                 google: "Playfair+Display:wght@400;600;700" },
    "cairo":   { label: "Cairo (Arabic-friendly)",
                 stack: '"Cairo","Segoe UI", sans-serif',
                 google: "Cairo:wght@400;600;700" },
  };

  function applyTheme(name) {
    const t = THEMES[name] || THEMES.light;
    const r = document.documentElement.style;
    r.setProperty("--primary", t.primary);
    r.setProperty("--primary-dark", t.primaryDark);
    r.setProperty("--accent", t.accent);
    r.setProperty("--bg", t.bg);
    r.setProperty("--surface", t.surface);
    r.setProperty("--text", t.text);
    r.setProperty("--muted", t.muted);
    r.setProperty("--border", t.border);
    document.documentElement.dataset.theme = name;
    localStorage.setItem(LS_THEME, name);
  }

  function applyFont(name) {
    const f = FONTS[name] || FONTS.system;
    document.documentElement.style.setProperty("--font", f.stack);
    document.body && (document.body.style.fontFamily = f.stack);
    document.documentElement.dataset.font = name;
    localStorage.setItem(LS_FONT, name);
    // Lazy-load Google font if needed
    if (f.google && !document.querySelector(`link[data-gfont="${name}"]`)) {
      const l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = `https://fonts.googleapis.com/css2?family=${f.google}&display=swap`;
      l.dataset.gfont = name;
      document.head.appendChild(l);
    }
  }

  // Public API
  window.lumoraThemes = THEMES;
  window.lumoraFonts = FONTS;
  window.lumoraSetTheme = applyTheme;
  window.lumoraSetFont = applyFont;
  window.lumoraOpenSettings = openSettingsPanel;

  // Apply on load
  applyTheme(localStorage.getItem(LS_THEME) || "light");
  applyFont(localStorage.getItem(LS_FONT) || "system");

  function openSettingsPanel() {
    const exist = document.getElementById("lumora-settings");
    if (exist) { exist.remove(); return; }
    const tpl = document.createElement("div");
    tpl.id = "lumora-settings";
    tpl.innerHTML = `
      <style>
        #lumora-settings { position:fixed; top:64px; inset-inline-end:16px; width:280px;
          background: var(--surface); color: var(--text); border-radius: 14px;
          padding: 18px; box-shadow: 0 16px 40px rgba(15,23,42,.18); z-index: 9999;
          border: 1px solid var(--border); }
        #lumora-settings h4 { margin: 0 0 8px; font-size: 12px; text-transform: uppercase;
          letter-spacing: 0.06em; color: var(--muted); }
        #lumora-settings .ts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin-bottom: 14px; }
        #lumora-settings .ts-grid button {
          padding: 10px; border: 1px solid var(--border); border-radius: 8px;
          background: var(--bg); cursor: pointer; font-size: 13px; color: var(--text);
        }
        #lumora-settings .ts-grid button.active { background: var(--primary); color: #fff; border-color: var(--primary); }
      </style>
      <h4>Theme</h4>
      <div class="ts-grid" id="ls-themes">
        ${Object.entries(THEMES).map(([k,v]) => `<button data-th="${k}">${v.label}</button>`).join("")}
      </div>
      <h4>Font</h4>
      <div class="ts-grid" id="ls-fonts" style="grid-template-columns:1fr">
        ${Object.entries(FONTS).map(([k,v]) => `<button data-ft="${k}">${v.label}</button>`).join("")}
      </div>
      <button onclick="document.getElementById('lumora-settings').remove()" style="margin-top:6px;width:100%;padding:8px;border:0;background:transparent;color:var(--muted);cursor:pointer">Close</button>
    `;
    document.body.appendChild(tpl);
    function refresh() {
      tpl.querySelectorAll("[data-th]").forEach(b =>
        b.classList.toggle("active", b.dataset.th === document.documentElement.dataset.theme));
      tpl.querySelectorAll("[data-ft]").forEach(b =>
        b.classList.toggle("active", b.dataset.ft === document.documentElement.dataset.font));
    }
    refresh();
    tpl.querySelector("#ls-themes").addEventListener("click", e => {
      const t = e.target.closest("[data-th]"); if (!t) return;
      applyTheme(t.dataset.th); refresh();
    });
    tpl.querySelector("#ls-fonts").addEventListener("click", e => {
      const t = e.target.closest("[data-ft]"); if (!t) return;
      applyFont(t.dataset.ft); refresh();
    });
  }
})();
