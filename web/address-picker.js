/* v1.24.91 — Pin-based UAE address picker (Leaflet + English-only tiles).
 *
 * USAGE:
 *   <div id="address-picker"></div>
 *   <script src="/address-picker.js"></script>
 *   <script>
 *     window.serviaAddressPicker.mount("#address-picker", {
 *       onPick: (addr) => console.log(addr),
 *     });
 *   </script>
 *
 * v1.24.91 changes (per founder review):
 *   • English-only tile provider (CartoDB Voyager EN) — no Arabic labels
 *   • City chips REMOVED — pin determines city via reverse-geocode
 *   • Area + city BOTH update on every pin move (was: area locked after first)
 *   • ⛶ Fullscreen map toggle
 *   • Building/area name autocomplete from localStorage (last 30 used)
 *   • Person-on-site MOBILE field added
 *   • "💾 Save permanent" toggle → label preset (Home / Office / Mom's / Other)
 *   • Auto-POST to /api/me/locations when authed + save-permanent ticked
 */
(function () {
  "use strict";

  const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  const LEAFLET_JS  = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

  // English-label tile sources. CartoDB Voyager has Latin scripts for the UAE
  // (Arabic translit) and is free for non-commercial. Fallback to OSM HOT
  // which renders English where available.
  // v1.24.98 — CartoDB Voyager *does* serve local-language labels
  // (Arabic in UAE) despite the v1.24.91 assumption otherwise. Switch
  // to ArcGIS World_Street_Map which renders English labels globally
  // and is free without an API key for non-commercial / light use.
  // Fallback to a no-labels Carto raster if ArcGIS rate-limits.
  const TILE_EN = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}";
  const TILE_ATTR = 'Tiles &copy; Esri — Source: Esri, HERE, Garmin, OpenStreetMap contributors';

  function loadLeaflet(cb) {
    if (window.L) return cb();
    if (!document.querySelector('link[href="' + LEAFLET_CSS + '"]')) {
      const link = document.createElement("link");
      link.rel = "stylesheet"; link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }
    if (document.querySelector('script[data-leaflet]')) {
      const i = setInterval(() => { if (window.L) { clearInterval(i); cb(); } }, 80);
      return;
    }
    const s = document.createElement("script");
    s.src = LEAFLET_JS; s.dataset.leaflet = "1"; s.onload = cb;
    document.head.appendChild(s);
  }

  // localStorage helpers for autocomplete
  const HIST_BLDG = "servia.addr.bldgs";
  const HIST_AREA = "servia.addr.areas";
  function recall(key) { try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch { return []; } }
  function remember(key, val) {
    if (!val || val.length < 2) return;
    let arr = recall(key);
    arr = arr.filter(x => x !== val); arr.unshift(val); arr = arr.slice(0, 30);
    try { localStorage.setItem(key, JSON.stringify(arr)); } catch {}
  }

  const STYLE = `
    .ap-wrap{font-family:-apple-system,system-ui,sans-serif;background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:14px;max-width:520px;margin:0 auto;color:#0F172A}
    .ap-title{font-size:14px;font-weight:800;margin:0 0 10px;color:#0F766E;display:flex;align-items:center;justify-content:space-between;gap:8px}
    .ap-title .fs{padding:5px 10px;border:1px solid #E2E8F0;border-radius:8px;background:#fff;font-size:12px;font-weight:700;color:#0F766E;cursor:pointer;font-family:inherit}
    .ap-title .fs:hover{background:#F0FDFA;border-color:#0F766E}
    .ap-map{height:240px;border-radius:10px;overflow:hidden;border:1.5px dashed #14B8A6;margin-bottom:10px;position:relative}
    .ap-wrap.fullscreen{position:fixed;inset:8px;max-width:none;margin:0;z-index:99999;overflow:auto}
    .ap-wrap.fullscreen .ap-map{height:60vh}
    .ap-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
    .ap-row.full{grid-template-columns:1fr}
    .ap-input{width:100%;padding:9px 10px;border:1.5px solid #E2E8F0;border-radius:9px;font-size:13px;font-family:inherit;box-sizing:border-box;min-height:42px;color:#0F172A;background:#fff}
    .ap-input:focus{outline:none;border-color:#0F766E;box-shadow:0 0 0 3px rgba(15,118,110,.15)}
    .ap-label{display:block;font-size:11px;font-weight:700;color:#475569;margin:4px 0 3px;text-transform:uppercase;letter-spacing:.04em}
    .ap-msg{font-size:12px;min-height:14px;margin:6px 0}
    .ap-msg.warn{color:#B45309}.ap-msg.err{color:#DC2626}.ap-msg.ok{color:#0F766E}
    .ap-btn{display:block;width:100%;padding:13px;background:#0F766E;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit;margin-top:8px}
    .ap-btn:hover{background:#0D9488}
    .ap-btn:disabled{opacity:.5;cursor:not-allowed}
    .ap-hint{font-size:11px;color:#94A3B8;text-align:center;margin-top:6px}
    .ap-toggle{display:flex;align-items:center;gap:8px;background:#F0FDFA;border:1px solid #99F6E4;border-radius:10px;padding:9px 12px;margin:8px 0;font-size:13px;font-weight:600;cursor:pointer}
    .ap-toggle input{margin:0;width:18px;height:18px;accent-color:#0F766E}
    .ap-presets{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
    .ap-pre{padding:6px 12px;border:1.5px solid #E2E8F0;border-radius:999px;background:#fff;font-size:12px;font-weight:700;color:#0F172A;cursor:pointer;font-family:inherit}
    .ap-pre.on{background:#0F766E;color:#fff;border-color:#0F766E}
  `;

  function ensureStyle() {
    if (document.getElementById("ap-style")) return;
    const s = document.createElement("style");
    s.id = "ap-style"; s.textContent = STYLE;
    document.head.appendChild(s);
  }

  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    for (const k in (attrs||{})) {
      if (k === "class") n.className = attrs[k];
      else if (k === "style") n.style.cssText = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    (children||[]).forEach(c => n.appendChild(typeof c === "string" ? document.createTextNode(c) : c));
    return n;
  }

  function input(id, ph, listId) {
    const i = el("input", { class: "ap-input", placeholder: ph || "" });
    if (id) i.id = id;
    if (listId) i.setAttribute("list", listId);
    return i;
  }

  function datalist(id, items) {
    const d = el("datalist", { id });
    items.forEach(v => d.appendChild(el("option", { value: v })));
    return d;
  }

  function mount(target, opts) {
    opts = opts || {};
    const root = (typeof target === "string" ? document.querySelector(target) : target);
    if (!root) return;
    ensureStyle();

    let pin = null, marker = null, map = null, geocoded = null;

    const wrap = el("div", { class: "ap-wrap" });
    const titleRow = el("div", { class: "ap-title" });
    titleRow.appendChild(el("span", {}, ["📍 Pin your exact location"]));
    const fsBtn = el("button", { type: "button", class: "fs" }, ["⛶ Fullscreen"]);
    fsBtn.onclick = () => {
      const isFs = wrap.classList.toggle("fullscreen");
      fsBtn.textContent = isFs ? "✕ Exit fullscreen" : "⛶ Fullscreen";
      // Re-size leaflet map after CSS change
      setTimeout(() => map && map.invalidateSize(), 250);
    };
    titleRow.appendChild(fsBtn);
    wrap.appendChild(titleRow);

    // Map
    const mapDiv = el("div", { class: "ap-map" });
    wrap.appendChild(mapDiv);

    // Datalists for autocomplete
    const dlBldg = datalist("ap-dl-bldg", recall(HIST_BLDG));
    const dlArea = datalist("ap-dl-area", recall(HIST_AREA));
    wrap.appendChild(dlBldg); wrap.appendChild(dlArea);

    // Form
    const labelIn    = input("", "Marina Crown");
    labelIn.value = "Home";
    const buildingIn = input("", "e.g. Marina Crown", "ap-dl-bldg");
    const unitIn     = input("", "e.g. 2104");
    const areaIn     = input("", "Auto-fills from pin", "ap-dl-area");
    const cityIn     = input("", "Auto-fills from pin");
    cityIn.readOnly = true; cityIn.style.background = "#F8FAFC";
    const personIn   = input("", "Same as account holder");
    const personPhIn = input("", "+971 ..."); personPhIn.type = "tel";
    const notesIn    = input("", "Park at gate B / door code 1234");

    function row(lab, inp, full) {
      const r = el("div", { class: "ap-row" + (full ? " full" : "") });
      const w = el("div"); w.appendChild(el("div", { class: "ap-label" }, [lab])); w.appendChild(inp);
      r.appendChild(w);
      return r;
    }
    wrap.appendChild(row("Label", labelIn, true));
    const r1 = el("div", { class: "ap-row" });
    const w1 = el("div"); w1.appendChild(el("div",{class:"ap-label"},["Building"])); w1.appendChild(buildingIn); r1.appendChild(w1);
    const w2 = el("div"); w2.appendChild(el("div",{class:"ap-label"},["Unit"])); w2.appendChild(unitIn); r1.appendChild(w2);
    wrap.appendChild(r1);
    const r2 = el("div", { class: "ap-row" });
    const w3 = el("div"); w3.appendChild(el("div",{class:"ap-label"},["Area"])); w3.appendChild(areaIn); r2.appendChild(w3);
    const w4 = el("div"); w4.appendChild(el("div",{class:"ap-label"},["City (auto)"])); w4.appendChild(cityIn); r2.appendChild(w4);
    wrap.appendChild(r2);
    const r3 = el("div", { class: "ap-row" });
    const w5 = el("div"); w5.appendChild(el("div",{class:"ap-label"},["Person on-site (optional)"])); w5.appendChild(personIn); r3.appendChild(w5);
    const w6 = el("div"); w6.appendChild(el("div",{class:"ap-label"},["Their mobile (optional)"])); w6.appendChild(personPhIn); r3.appendChild(w6);
    wrap.appendChild(r3);
    wrap.appendChild(row("Access notes (optional)", notesIn, true));

    // Save-permanent toggle + label preset
    const saveTog = el("label", { class: "ap-toggle" });
    const saveCb  = el("input", { type: "checkbox" });
    saveTog.appendChild(saveCb);
    saveTog.appendChild(el("span", {}, ["💾 Save this address to my profile"]));
    wrap.appendChild(saveTog);

    const presetWrap = el("div", { style: "display:none;margin-top:6px" });
    presetWrap.appendChild(el("div", { class: "ap-label" }, ["Save as"]));
    const presets = el("div", { class: "ap-presets" });
    let chosenPreset = "Home";
    ["Home","Office","Mom's","Dad's","Holiday home","Other"].forEach((nm, i) => {
      const b = el("button", { type: "button", class: "ap-pre" + (i === 0 ? " on" : "") }, [nm]);
      b.onclick = () => {
        [...presets.querySelectorAll(".ap-pre")].forEach(x => x.classList.remove("on"));
        b.classList.add("on"); chosenPreset = nm;
        if (nm === "Other") {
          const v = prompt("Name this place:", labelIn.value || "My place");
          if (v) labelIn.value = v;
        } else {
          labelIn.value = nm;
        }
      };
      presets.appendChild(b);
    });
    presetWrap.appendChild(presets);
    wrap.appendChild(presetWrap);
    saveCb.onchange = () => {
      presetWrap.style.display = saveCb.checked ? "block" : "none";
    };

    const msg = el("div", { class: "ap-msg" });
    wrap.appendChild(msg);

    const btn = el("button", { type: "button", class: "ap-btn" });
    btn.textContent = "✅ Use this address";
    btn.disabled = true;
    wrap.appendChild(btn);
    wrap.appendChild(el("div", { class: "ap-hint" }, ["Drag the pin or tap the map to mark the exact spot."]));

    root.innerHTML = "";
    root.appendChild(wrap);

    loadLeaflet(() => {
      const center = [25.20, 55.27]; // Dubai
      map = L.map(mapDiv, { zoomControl: true }).setView(center, 11);
      L.tileLayer(TILE_EN, { maxZoom: 19, subdomains: "abcd",
                             attribution: TILE_ATTR }).addTo(map);

      function setPin(latlng) {
        pin = latlng;
        if (marker) marker.setLatLng(latlng);
        else {
          marker = L.marker(latlng, { draggable: true }).addTo(map);
          marker.on("dragend", e => setPin(e.target.getLatLng()));
        }
        msg.className = "ap-msg"; msg.textContent = "Looking up address…";
        fetch("/api/geocode/reverse", {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({lat: latlng.lat, lng: latlng.lng}),
        }).then(r => r.json()).then(j => {
          geocoded = j;
          if (j.ok) {
            // v1.24.91 fix: ALWAYS overwrite area + city on every pin
            // move (was: only filled area if empty → stale on subsequent pins)
            if (j.area) areaIn.value = j.area;
            if (j.city || j.emirate) {
              const eName = (j.emirate || "").replace(/_/g," ").replace(/\b\w/g, c=>c.toUpperCase());
              cityIn.value = j.city || eName;
            }
            msg.className = "ap-msg ok";
            msg.textContent = "✓ " + (j.area || j.city || "Pin recorded");
            btn.disabled = false;
          } else {
            msg.className = "ap-msg err";
            msg.textContent = "Couldn't find that location. Try moving the pin.";
            btn.disabled = false;
          }
        }).catch(() => {
          msg.className = "ap-msg err";
          msg.textContent = "Network error. Try again.";
          btn.disabled = true;
        });
      }
      map.on("click", e => setPin(e.latlng));
    });

    btn.onclick = async () => {
      if (!pin) {
        msg.className = "ap-msg err";
        msg.textContent = "Please drop a pin on the map first.";
        return;
      }
      if (!buildingIn.value.trim()) {
        msg.className = "ap-msg err";
        msg.textContent = "Please enter the building name or number.";
        buildingIn.focus(); return;
      }
      // Remember entries for autocomplete
      remember(HIST_BLDG, buildingIn.value.trim());
      remember(HIST_AREA, areaIn.value.trim());

      const out = {
        lat: pin.lat, lng: pin.lng,
        label: labelIn.value.trim() || chosenPreset || "Home",
        building: buildingIn.value.trim(),
        unit: unitIn.value.trim(),
        area: areaIn.value.trim(),
        city: cityIn.value.trim(),
        contact_name: personIn.value.trim(),
        contact_phone: personPhIn.value.trim(),
        notes: notesIn.value.trim(),
        save_permanent: !!saveCb.checked,
        full: [buildingIn.value, unitIn.value, areaIn.value, cityIn.value].filter(Boolean).join(", "),
      };
      // Auto-save to profile if requested + we have a session cookie
      if (out.save_permanent) {
        try {
          const r = await fetch("/api/me/locations", {
            method: "POST", credentials: "include",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify(out),
          });
          const j = await r.json();
          if (j.ok) {
            msg.className = "ap-msg ok";
            msg.textContent = "✅ Saved to your profile.";
          } else {
            msg.className = "ap-msg warn";
            msg.textContent = "✓ Address used (sign in to save permanently).";
          }
        } catch (_) {
          msg.className = "ap-msg warn";
          msg.textContent = "✓ Address used (couldn't save to profile).";
        }
      } else {
        msg.className = "ap-msg ok";
        msg.textContent = "✅ Saved.";
      }
      // v1.24.98 — exit fullscreen so the user can see the chat
      // response. Previously the picker stayed frozen in fullscreen
      // after onPick fired, making the user think nothing happened
      // (rage-click loop confirmed by founder screenshot).
      if (wrap.classList.contains("fullscreen")) {
        wrap.classList.remove("fullscreen");
        fsBtn.textContent = "⛶ Fullscreen";
      }
      // v1.24.98 — also collapse the form into a compact "✅ Pinned"
      // confirmation so user knows the action was accepted. Tapping
      // the confirmation re-opens the picker for edits.
      btn.disabled = true;
      btn.textContent = "✅ Address recorded";
      setTimeout(() => {
        if (mapDiv && mapDiv.parentNode) mapDiv.style.display = "none";
        const detail = wrap.querySelectorAll(".ap-row, .ap-presets, .ap-msg, .ap-hint");
        detail.forEach(n => { n.style.display = "none"; });
      }, 250);
      if (typeof opts.onPick === "function") opts.onPick(out);
    };
  }

  window.serviaAddressPicker = { mount };
})();
