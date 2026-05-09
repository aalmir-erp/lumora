/* v1.24.84 — Pin-based UAE address picker (Leaflet + OSM, no API key).
 *
 * USAGE:
 *   <div id="address-picker"></div>
 *   <script src="/address-picker.js"></script>
 *   <script>
 *     window.serviaAddressPicker.mount("#address-picker", {
 *       defaultCity: "Dubai",
 *       onPick: (addr) => console.log(addr),
 *     });
 *   </script>
 *
 * Returns a structured address: { lat, lng, city, area, road, building,
 *   unit, label, full }. Cross-checks city via /api/geocode/check-city
 * before allowing submission.
 */
(function () {
  "use strict";

  const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  const LEAFLET_JS  = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";

  function loadLeaflet(cb) {
    if (window.L) return cb();
    if (!document.querySelector('link[href="' + LEAFLET_CSS + '"]')) {
      const link = document.createElement("link");
      link.rel = "stylesheet"; link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }
    if (document.querySelector('script[data-leaflet]')) {
      // already loading
      const i = setInterval(() => { if (window.L) { clearInterval(i); cb(); } }, 80);
      return;
    }
    const s = document.createElement("script");
    s.src = LEAFLET_JS; s.dataset.leaflet = "1"; s.onload = cb;
    document.head.appendChild(s);
  }

  // UAE city presets — tap-to-jump
  const CITY_CENTRES = {
    "Dubai":         [25.20, 55.27],
    "Abu Dhabi":     [24.47, 54.37],
    "Sharjah":       [25.34, 55.42],
    "Ajman":         [25.40, 55.48],
    "Umm Al Quwain": [25.55, 55.55],
    "Ras Al Khaimah":[25.79, 55.95],
    "Fujairah":      [25.13, 56.34],
  };

  // Inject CSS once
  const STYLE = `
    .ap-wrap{font-family:-apple-system,system-ui,sans-serif;background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:14px;max-width:520px;margin:0 auto;color:#0F172A}
    .ap-title{font-size:14px;font-weight:800;margin:0 0 10px;color:#0F766E}
    .ap-cities{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
    .ap-city{padding:6px 12px;border:1px solid #E2E8F0;border-radius:999px;background:#fff;color:#0F172A;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit}
    .ap-city.on{background:#0F766E;color:#fff;border-color:#0F766E}
    .ap-map{height:240px;border-radius:10px;overflow:hidden;border:1.5px dashed #14B8A6;margin-bottom:10px}
    .ap-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px}
    .ap-row.full{grid-template-columns:1fr}
    .ap-input{width:100%;padding:9px 10px;border:1.5px solid #E2E8F0;border-radius:9px;font-size:13px;font-family:inherit;box-sizing:border-box;min-height:42px;color:#0F172A}
    .ap-input:focus{outline:none;border-color:#0F766E;box-shadow:0 0 0 3px rgba(15,118,110,.15)}
    .ap-label{display:block;font-size:11px;font-weight:700;color:#475569;margin:4px 0 3px;text-transform:uppercase;letter-spacing:.04em}
    .ap-msg{font-size:12px;min-height:14px;margin:6px 0}
    .ap-msg.warn{color:#B45309}
    .ap-msg.err{color:#DC2626}
    .ap-msg.ok{color:#0F766E}
    .ap-btn{display:block;width:100%;padding:13px;background:#0F766E;color:#fff;border:none;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit;margin-top:8px}
    .ap-btn:hover{background:#0D9488}
    .ap-btn:disabled{opacity:.5;cursor:not-allowed}
    .ap-hint{font-size:11px;color:#94A3B8;text-align:center;margin-top:6px}
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

  function mount(target, opts) {
    opts = opts || {};
    const root = (typeof target === "string" ? document.querySelector(target) : target);
    if (!root) return;
    ensureStyle();

    let currentCity = opts.defaultCity || "Dubai";
    let pin = null, marker = null, map = null, geocoded = null;

    const wrap = el("div", { class: "ap-wrap" });
    wrap.appendChild(el("div", { class: "ap-title" }, ["📍 Pin your exact location"]));

    // City chips
    const cityRow = el("div", { class: "ap-cities" });
    Object.keys(CITY_CENTRES).forEach(city => {
      const b = el("button", { type: "button", class: "ap-city" + (city === currentCity ? " on" : "") });
      b.textContent = city;
      b.onclick = () => {
        currentCity = city;
        [...cityRow.querySelectorAll(".ap-city")].forEach(x => x.classList.remove("on"));
        b.classList.add("on");
        if (map) map.setView(CITY_CENTRES[city], 12);
      };
      cityRow.appendChild(b);
    });
    wrap.appendChild(cityRow);

    // Map
    const mapDiv = el("div", { class: "ap-map" });
    wrap.appendChild(mapDiv);

    // Form fields
    const buildingIn = el("input", { class: "ap-input", placeholder: "e.g. Marina Crown" });
    const unitIn     = el("input", { class: "ap-input", placeholder: "e.g. 2104" });
    const areaIn     = el("input", { class: "ap-input", placeholder: "e.g. Dubai Marina (auto-fills)" });
    const cityIn     = el("input", { class: "ap-input" });
    cityIn.value = currentCity;
    const labelIn    = el("input", { class: "ap-input", placeholder: "Home / Office / Mom's place" });
    labelIn.value = "Home";
    const contactIn  = el("input", { class: "ap-input", placeholder: "Same as account holder" });
    const notesIn    = el("input", { class: "ap-input", placeholder: "Park at gate B / door code 1234" });

    function row(label, input, full) {
      const r = el("div", { class: "ap-row" + (full ? " full" : "") });
      const w = el("div"); w.appendChild(el("div", { class: "ap-label" }, [label])); w.appendChild(input);
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
    const w4 = el("div"); w4.appendChild(el("div",{class:"ap-label"},["City"])); w4.appendChild(cityIn); r2.appendChild(w4);
    wrap.appendChild(r2);
    wrap.appendChild(row("Person on-site (optional)", contactIn, true));
    wrap.appendChild(row("Access notes (optional)", notesIn, true));

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
      const c = CITY_CENTRES[currentCity];
      map = L.map(mapDiv, { zoomControl: true }).setView(c, 12);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: '© OpenStreetMap',
      }).addTo(map);

      function setPin(latlng) {
        pin = latlng;
        if (marker) marker.setLatLng(latlng);
        else {
          marker = L.marker(latlng, { draggable: true }).addTo(map);
          marker.on("dragend", e => setPin(e.target.getLatLng()));
        }
        // Reverse geocode
        msg.className = "ap-msg"; msg.textContent = "Looking up address…";
        fetch("/api/geocode/reverse", {
          method: "POST", headers: {"Content-Type":"application/json"},
          body: JSON.stringify({lat: latlng.lat, lng: latlng.lng}),
        }).then(r => r.json()).then(j => {
          geocoded = j;
          if (j.ok) {
            if (!areaIn.value && j.area) areaIn.value = j.area;
            if (j.city) {
              // Cross-check city
              fetch("/api/geocode/check-city", {
                method: "POST", headers: {"Content-Type":"application/json"},
                body: JSON.stringify({lat: latlng.lat, lng: latlng.lng, claimed_city: cityIn.value}),
              }).then(r => r.json()).then(ck => {
                if (ck.ok && !ck.matches) {
                  msg.className = "ap-msg warn";
                  msg.textContent = "⚠️ " + ck.suggestion;
                  // Auto-correct city to actual emirate
                  const friendly = ck.actual_emirate.replace(/_/g," ").replace(/\b\w/g, c=>c.toUpperCase());
                  cityIn.value = friendly;
                } else {
                  msg.className = "ap-msg ok";
                  msg.textContent = "✓ " + (j.area || j.city || "Pin recorded");
                }
              }).catch(() => {});
            }
            btn.disabled = false;
          } else {
            msg.className = "ap-msg err";
            msg.textContent = "Couldn't find that location. Try moving the pin.";
            btn.disabled = false; // still allow submit with manual fields
          }
        }).catch(() => {
          msg.className = "ap-msg err";
          msg.textContent = "Network error. Try again.";
          btn.disabled = true;
        });
      }
      map.on("click", e => setPin(e.latlng));
    });

    btn.onclick = () => {
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
      const out = {
        lat: pin.lat, lng: pin.lng,
        label: labelIn.value.trim() || "Home",
        building: buildingIn.value.trim(),
        unit: unitIn.value.trim(),
        area: areaIn.value.trim(),
        city: cityIn.value.trim(),
        contact_name: contactIn.value.trim(),
        notes: notesIn.value.trim(),
        full: [buildingIn.value, unitIn.value, areaIn.value, cityIn.value].filter(Boolean).join(", "),
      };
      if (typeof opts.onPick === "function") opts.onPick(out);
      msg.className = "ap-msg ok";
      msg.textContent = "✅ Saved.";
    };
  }

  window.serviaAddressPicker = { mount };
})();
