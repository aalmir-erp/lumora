/* Servia location-permission bar.
 *
 * Shows a slim teal strip at the top of every public page (just under the
 * rotating banner). Asks the user for browser geolocation, reverse-geocodes
 * via OpenStreetMap Nominatim, then displays "📍 Detected: Dubai Marina"
 * with an Edit-address button. Tap Edit → modal sheet to fill in full
 * structured address (building, apartment, street, contact, notes).
 *
 * Side-effects we surface from the saved address:
 *   - All ?service= deep-links pre-fill the address form server-side
 *   - Home page quick-service tiles get an "Available now in <area>" badge
 *   - Logged-in customers' addresses sync to the server (saved-addresses table)
 *
 * The bar dismisses for the session if the user closes it. localStorage
 * remembers their detected/manual address forever (or until they clear).
 */
(function () {
  if (window.__servia_location_bar) return;
  window.__servia_location_bar = true;

  // Skip on internal / admin / payment / vendor pages
  if (/^\/(admin|vendor|portal|pay|invoice)/.test(location.pathname)) return;

  const KEY_LOC = "servia.user.location.v1";       // {area, emirate, lat, lng, full_address, ...}
  const KEY_DISMISSED = "servia.location.dismissed_session";

  // Don't bother if dismissed this session
  try {
    if (sessionStorage.getItem(KEY_DISMISSED) === "1") return;
  } catch (_) {}

  // CSS for the slim bar + modal
  const css = document.createElement("style");
  css.textContent = `
    #servia-loc-bar {
      position:relative; width:100%; min-height:36px; box-sizing:border-box;
      background:linear-gradient(90deg,#0F766E,#14B8A6);
      color:#fff; font-size:13px; font-weight:600; line-height:1.3;
      padding:7px 14px; display:flex; gap:10px; align-items:center;
      flex-wrap:wrap; box-shadow:0 2px 6px rgba(15,23,42,.08);
    }
    #servia-loc-bar.compact { padding:6px 14px; min-height:32px; font-size:12.5px; }
    #servia-loc-bar .pin { font-size:14px; }
    #servia-loc-bar .label { flex:1; min-width:140px; }
    #servia-loc-bar .label b { color:#FCD34D; font-weight:800; }
    #servia-loc-bar button {
      background:rgba(255,255,255,.18); color:#fff; border:1px solid rgba(255,255,255,.28);
      padding:4px 10px; border-radius:999px; font-weight:700; font-size:11.5px;
      cursor:pointer; line-height:1; flex-shrink:0;
    }
    #servia-loc-bar button:hover { background:rgba(255,255,255,.28); }
    #servia-loc-bar .x {
      background:transparent; border:0; color:rgba(255,255,255,.7);
      font-size:14px; padding:0 4px; flex-shrink:0;
    }
    #servia-loc-bar .x:hover { color:#fff; }

    /* Detected-location pulse */
    @keyframes servia-loc-pulse { 0%,100% { opacity:1 } 50% { opacity:.6 } }
    #servia-loc-bar .detecting .dot {
      display:inline-block; width:6px; height:6px; border-radius:50%;
      background:#FCD34D; animation:servia-loc-pulse 1.2s infinite;
      vertical-align:middle; margin-inline-end:4px;
    }

    /* Modal sheet */
    #servia-loc-modal {
      position:fixed; inset:0; background:rgba(15,23,42,.55);
      backdrop-filter:blur(4px); z-index:99998;
      display:flex; align-items:flex-end; justify-content:center;
      animation:slfade .2s ease;
    }
    @keyframes slfade { from { opacity:0 } to { opacity:1 } }
    #servia-loc-modal .sheet {
      background:#fff; width:100%; max-width:520px;
      border-radius:24px 24px 0 0; padding:22px 22px 28px;
      max-height:88vh; overflow:auto;
      box-shadow:0 -16px 40px rgba(15,23,42,.18);
      animation:slup .25s ease;
    }
    @keyframes slup { from { transform:translateY(40px) } to { transform:translateY(0) } }
    #servia-loc-modal h3 { margin:0 0 6px; font-size:20px; letter-spacing:-.01em; }
    #servia-loc-modal .sub { color:#64748B; font-size:13px; margin:0 0 14px; }
    #servia-loc-modal .row { margin-bottom:10px; }
    #servia-loc-modal label {
      display:block; font-size:11.5px; color:#475569; font-weight:700;
      margin-bottom:4px; text-transform:uppercase; letter-spacing:.04em;
    }
    #servia-loc-modal input, #servia-loc-modal select, #servia-loc-modal textarea {
      width:100%; padding:11px 12px; border:1.5px solid #E2E8F0;
      border-radius:10px; font-size:14px; font-family:inherit;
      box-sizing:border-box;
    }
    #servia-loc-modal input:focus, #servia-loc-modal select:focus {
      outline:none; border-color:#0D9488;
    }
    #servia-loc-modal .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    @media (max-width:480px) { #servia-loc-modal .grid2 { grid-template-columns:1fr } }
    #servia-loc-modal .actions {
      display:flex; gap:8px; margin-top:14px;
    }
    #servia-loc-modal .actions button {
      flex:1; padding:13px; border:0; border-radius:12px; font-weight:700;
      font-size:14px; cursor:pointer; line-height:1;
    }
    #servia-loc-modal .actions .save {
      background:linear-gradient(135deg,#0F766E,#14B8A6); color:#fff;
    }
    #servia-loc-modal .actions .skip {
      background:#F1F5F9; color:#475569;
    }
    /* Tag chips */
    #servia-loc-modal .tag-chips {
      display:flex; flex-wrap:wrap; gap:6px; margin-bottom:6px;
    }
    #servia-loc-modal .tag-chip {
      padding:8px 14px; border:1.5px solid #E2E8F0; background:#fff;
      border-radius:999px; font-size:13px; font-weight:600; color:#475569;
      cursor:pointer; line-height:1.1; display:inline-flex; align-items:center; gap:5px;
      transition:.12s; font-family:inherit;
    }
    #servia-loc-modal .tag-chip:hover { border-color:#0F766E; color:#0F766E; }
    #servia-loc-modal .tag-chip.active {
      background:linear-gradient(135deg,#0F766E,#14B8A6); color:#fff;
      border-color:#0F766E; box-shadow:0 4px 10px rgba(15,118,110,.25);
    }
    #servia-loc-modal .tag-chip.add-custom { border-style:dashed; color:#94A3B8; }
    #servia-loc-modal #lm-tag-custom {
      width:auto; max-width:160px; padding:6px 12px; font-size:13px;
      border-radius:999px; display:none;
    }
    #servia-loc-modal #lm-tag-custom.show { display:inline-block; }
    /* Map picker */
    #servia-loc-modal .map-toggle {
      display:flex; align-items:center; gap:8px; margin:8px 0 4px;
      padding:10px 12px; background:#F0FDFA; border:1.5px solid #99F6E4;
      border-radius:10px; cursor:pointer; font-size:13px; font-weight:600;
      color:#0F766E; user-select:none;
    }
    #servia-loc-modal .map-toggle:hover { background:#CCFBF1; }
    #servia-loc-modal .map-toggle .arr { margin-inline-start:auto; transition:transform .2s; }
    #servia-loc-modal .map-toggle.open .arr { transform:rotate(90deg); }
    #servia-loc-modal #lm-map-wrap {
      display:none; margin-top:8px; border-radius:12px; overflow:hidden;
      border:1.5px solid #E2E8F0;
    }
    #servia-loc-modal #lm-map-wrap.show { display:block; }
    #servia-loc-modal #lm-map { width:100%; height:260px; }
    #servia-loc-modal .map-hint {
      font-size:11.5px; color:#64748B; padding:6px 10px; background:#F8FAFC;
      border-top:1px solid #E2E8F0;
    }
    #servia-loc-modal .map-hint b { color:#0F766E; }
  `;
  document.head.appendChild(css);

  // Build bar element
  const bar = document.createElement("div");
  bar.id = "servia-loc-bar";
  bar.innerHTML = `
    <span class="pin">📍</span>
    <span class="label" id="servia-loc-label">
      <span class="detecting"><span class="dot"></span>Detecting your area for personalised service…</span>
    </span>
    <button type="button" id="servia-loc-grant" style="display:none">Allow location</button>
    <button type="button" id="servia-loc-pin" style="display:none" title="Pin location on map">🗺 Pin map</button>
    <button type="button" id="servia-loc-edit" style="display:none">Edit address</button>
    <button type="button" class="x" id="servia-loc-x" aria-label="Hide">✕</button>
  `;
  // Insert under the rotating banner / above the flag strip.
  // v1.23.1: prefer replacing the pre-rendered #servia-loc-bar-placeholder
  // so there's NO layout shift between SSR placeholder and real bar.
  function insertBar() {
    if (!document.body) return;
    const ph = document.getElementById("servia-loc-bar-placeholder");
    if (ph && ph.parentNode) {
      ph.parentNode.replaceChild(bar, ph);
    } else {
      const flag = document.querySelector(".uae-flag-strip");
      if (flag && flag.parentNode === document.body) {
        flag.parentNode.insertBefore(bar, flag.nextSibling);
      } else {
        document.body.insertBefore(bar, document.body.firstChild);
      }
    }
    document.body.classList.add("has-location-bar");
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", insertBar);
  } else {
    insertBar();
  }

  // Helper: read saved location
  function getSaved() {
    try { return JSON.parse(localStorage.getItem(KEY_LOC) || "null"); } catch { return null; }
  }
  function setSaved(o) {
    try { localStorage.setItem(KEY_LOC, JSON.stringify(o)); } catch (_) {}
    window.dispatchEvent(new CustomEvent("servia:location-changed", { detail: o }));
  }

  function renderBar() {
    const saved = getSaved();
    const lbl = document.getElementById("servia-loc-label");
    const grant = document.getElementById("servia-loc-grant");
    const edit = document.getElementById("servia-loc-edit");
    const pin = document.getElementById("servia-loc-pin");
    if (saved && saved.area) {
      const where = [saved.area, saved.emirate].filter(Boolean).join(", ");
      const tag = saved.tag ? `<span style="background:rgba(252,211,77,.25);color:#FCD34D;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:800;margin-inline-end:4px">${escapeHtml(saved.tag)}</span>` : "";
      lbl.innerHTML = `${tag}Servicing <b>${escapeHtml(where)}</b>${saved.full_address ? "" : " · add your full address for one-tap booking"}`;
      grant.style.display = "none";
      edit.style.display = "";
      if (pin) pin.style.display = "";    // v1.23.3 — show map-pin button when we have an area
      bar.classList.add("compact");
    } else {
      lbl.innerHTML = `<span class="detecting"><span class="dot"></span>Allow location for area-specific prices &amp; arrival ETAs</span>`;
      grant.style.display = "";
      edit.style.display = "";
      if (pin) pin.style.display = "none";
      grant.textContent = "Allow location";
      edit.textContent = "Set manually";
    }
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[<>&"']/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;","\"":"&quot;","'":"&#39;"}[c]));
  }

  // Wire bar buttons + initial render
  setTimeout(() => {
    renderBar();
    document.getElementById("servia-loc-grant").addEventListener("click", grantLocation);
    document.getElementById("servia-loc-edit").addEventListener("click", openEditModal);
    // v1.23.3 — Pin-map button: opens edit modal AND auto-expands the map section
    const pinBtn = document.getElementById("servia-loc-pin");
    if (pinBtn) pinBtn.addEventListener("click", () => {
      openEditModal();
      // After modal opens, click the map-toggle to expand it
      setTimeout(() => {
        const t = document.getElementById("lm-map-toggle");
        if (t && !t.classList.contains("open")) t.click();
      }, 100);
    });
    document.getElementById("servia-loc-x").addEventListener("click", () => {
      try { sessionStorage.setItem(KEY_DISMISSED, "1"); } catch (_) {}
      bar.style.display = "none";
    });
    // Auto-attempt geolocation if user hasn't saved anything AND hasn't denied
    if (!getSaved() && navigator.permissions) {
      navigator.permissions.query({ name:"geolocation" }).then(p => {
        if (p.state === "granted") grantLocation();
      }).catch(()=>{});
    }
  }, 50);

  function grantLocation() {
    if (!navigator.geolocation) {
      openEditModal();
      return;
    }
    document.getElementById("servia-loc-label").innerHTML =
      '<span class="detecting"><span class="dot"></span>Detecting your location…</span>';
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const { latitude: lat, longitude: lng } = pos.coords;
      const place = await reverseGeocode(lat, lng);
      const obj = {
        lat, lng,
        area: place.area || place.suburb || "",
        emirate: place.emirate || "",
        country: place.country || "United Arab Emirates",
        detected_at: new Date().toISOString(),
      };
      setSaved(obj);
      renderBar();
    }, () => {
      // Permission denied / error — fall back to manual entry
      openEditModal();
    }, { enableHighAccuracy:false, timeout:8000, maximumAge:600000 });
  }

  async function reverseGeocode(lat, lng) {
    try {
      const r = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&zoom=14&addressdetails=1`,
        { headers:{ "Accept":"application/json" } });
      const j = await r.json();
      const a = j.address || {};
      return {
        area: a.suburb || a.neighbourhood || a.city_district || a.village || a.town || "",
        suburb: a.suburb || "",
        emirate: a.state || a.region || "",
        country: a.country || "",
      };
    } catch (_) {
      return {};
    }
  }

  function openEditModal() {
    if (document.getElementById("servia-loc-modal")) return;
    const saved = getSaved() || {};
    const m = document.createElement("div");
    m.id = "servia-loc-modal";
    m.innerHTML = `
      <div class="sheet">
        <h3>📍 Where should we send the pro?</h3>
        <p class="sub">Drop your pin on the map below — that's the exact spot our crew arrives. Then fill in the building details.</p>

        <!-- v1.23.5 — Map FIRST, ALWAYS visible at top of modal. Per user
             request: 'edit address must take exact pin location'. The map
             is the headline section; form fields are secondary. -->
        <div id="lm-map-wrap" class="show" style="margin:0 0 14px;border-radius:14px;overflow:hidden;border:2px solid #14B8A6;box-shadow:0 12px 32px rgba(15,118,110,.18)">
          <div id="lm-map" style="width:100%;height:300px;background:#F0FDFA"></div>
          <div class="map-hint" style="background:#0F766E;color:#fff;padding:10px 14px;font-size:12.5px;line-height:1.4">
            <b style="color:#FCD34D">📍 Drag the pin</b> to the exact spot. Address fields below auto-fill from the pin's location.
          </div>
        </div>

        <div class="row">
          <label>Save as</label>
          <div class="tag-chips" id="lm-tag-chips">
            <button type="button" class="tag-chip" data-tag="Home">🏠 Home</button>
            <button type="button" class="tag-chip" data-tag="Work">🏢 Work</button>
            <button type="button" class="tag-chip" data-tag="Villa">🏡 Villa</button>
            <button type="button" class="tag-chip" data-tag="Hotel">🏨 Hotel</button>
            <button type="button" class="tag-chip" data-tag="Parents">👨‍👩‍👧 Parents</button>
            <button type="button" class="tag-chip" data-tag="Friend">💒 Friend</button>
            <button type="button" class="tag-chip" data-tag="Office 2">🏬 Office 2</button>
            <button type="button" class="tag-chip add-custom" id="lm-tag-add">＋ Custom</button>
            <input id="lm-tag-custom" placeholder="My label" maxlength="20">
          </div>
        </div>

        <div class="grid2">
          <div class="row">
            <label>Emirate</label>
            <select id="lm-emirate">
              <option value="">—</option>
              <option>Dubai</option>
              <option>Abu Dhabi</option>
              <option>Sharjah</option>
              <option>Ajman</option>
              <option>Ras Al Khaimah</option>
              <option>Umm Al Quwain</option>
              <option>Fujairah</option>
            </select>
          </div>
          <div class="row">
            <label>Area / Community</label>
            <input id="lm-area" placeholder="Dubai Marina, JVC, Tecom…">
          </div>
          <div class="row">
            <label>Building / Villa</label>
            <input id="lm-building" placeholder="Marina Tower 3">
          </div>
          <div class="row">
            <label>Apartment / Unit</label>
            <input id="lm-apartment" placeholder="2104">
          </div>
          <div class="row" style="grid-column:1/-1">
            <label>Street / Landmark</label>
            <input id="lm-street" placeholder="Al Marsa Street, near Spinneys">
          </div>
          <div class="row">
            <label>Contact name</label>
            <input id="lm-contact-name" placeholder="Mom" autocomplete="name">
          </div>
          <div class="row">
            <label>Contact phone</label>
            <input id="lm-contact-phone" placeholder="+971501234567" type="tel" inputmode="tel">
          </div>
          <div class="row" style="grid-column:1/-1">
            <label>Notes (gate code, parking, etc.)</label>
            <input id="lm-notes" placeholder="Gate 4242, parking P-12">
          </div>
        </div>

        <!-- v1.23.5: old toggle + duplicate map-wrap removed (map is now at TOP of modal, always visible) -->

        <div class="actions">
          <button class="skip" type="button" id="lm-skip">Skip for now</button>
          <button class="save" type="button" id="lm-save">Save address</button>
        </div>
      </div>
    `;
    document.body.appendChild(m);

    // Pre-fill any saved values
    setVal("lm-emirate", saved.emirate);
    setVal("lm-area", saved.area);
    setVal("lm-building", saved.building);
    setVal("lm-apartment", saved.apartment);
    setVal("lm-street", saved.street);
    setVal("lm-contact-name", saved.contact_name);
    setVal("lm-contact-phone", saved.contact_phone);
    setVal("lm-notes", saved.notes);

    // Tag chip handling: pick existing or create custom
    const chipsRow = document.getElementById("lm-tag-chips");
    const customInput = document.getElementById("lm-tag-custom");
    function selectChip(tag) {
      chipsRow.querySelectorAll(".tag-chip").forEach(c => c.classList.remove("active"));
      const match = chipsRow.querySelector(`.tag-chip[data-tag="${tag}"]`);
      if (match) match.classList.add("active");
      m.dataset.selectedTag = tag || "";
    }
    selectChip(saved.tag || "Home");
    chipsRow.addEventListener("click", e => {
      const c = e.target.closest(".tag-chip");
      if (!c) return;
      if (c.id === "lm-tag-add") {
        customInput.classList.add("show");
        customInput.focus();
        return;
      }
      selectChip(c.dataset.tag);
      customInput.classList.remove("show");
      customInput.value = "";
    });
    customInput.addEventListener("input", () => {
      const v = customInput.value.trim();
      if (v) {
        chipsRow.querySelectorAll(".tag-chip").forEach(c => c.classList.remove("active"));
        m.dataset.selectedTag = v;
      }
    });

    // v1.23.5 — map is at the TOP of the modal, always visible, no toggle.
    // Just init it as soon as the modal renders.
    setTimeout(() => initMap(saved.lat, saved.lng), 80);

    document.getElementById("lm-skip").onclick = () => m.remove();
    m.addEventListener("click", e => { if (e.target === m) m.remove(); });
    document.getElementById("lm-save").onclick = saveFromModal;
  }

  // Lazy-load Leaflet (~40KB) only when user opens the map picker.
  let _leafletLoaded = null;
  function loadLeaflet() {
    if (_leafletLoaded) return _leafletLoaded;
    _leafletLoaded = new Promise(res => {
      if (window.L) { res(window.L); return; }
      const css = document.createElement("link");
      css.rel = "stylesheet";
      css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(css);
      const s = document.createElement("script");
      s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      s.onload = () => res(window.L);
      s.onerror = () => res(null);
      document.head.appendChild(s);
    });
    return _leafletLoaded;
  }

  let _map = null, _marker = null;
  async function initMap(lat, lng) {
    const L = await loadLeaflet();
    if (!L) return;
    // Default to Dubai Marina if no saved coordinates
    const c = [lat || 25.0772, lng || 55.1396];
    if (_map) {
      _map.setView(c, 15);
      _marker.setLatLng(c);
      // Force tile recalc since modal can resize
      setTimeout(() => _map.invalidateSize(), 80);
      return;
    }
    _map = L.map("lm-map", { zoomControl: true }).setView(c, lat ? 16 : 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '© OpenStreetMap',
    }).addTo(_map);
    _marker = L.marker(c, { draggable: true }).addTo(_map);
    _marker.on("dragend", async () => {
      const p = _marker.getLatLng();
      await reverseGeocodePin(p.lat, p.lng);
    });
    _map.on("click", e => {
      _marker.setLatLng(e.latlng);
      reverseGeocodePin(e.latlng.lat, e.latlng.lng);
    });
    setTimeout(() => _map.invalidateSize(), 120);
  }

  async function reverseGeocodePin(lat, lng) {
    try {
      const r = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&addressdetails=1&zoom=18`,
        { headers: { "Accept-Language": "en" } }
      );
      if (!r.ok) return;
      const j = await r.json();
      const a = j.address || {};
      // Best-effort UAE area extraction
      const area = a.suburb || a.neighbourhood || a.quarter || a.village ||
                    a.city_district || a.town || a.district || "";
      const emirate = (a.state || a.region || "").replace(" Emirate", "").trim();
      const street = a.road || "";
      if (area)    setVal("lm-area", area);
      if (emirate) setVal("lm-emirate", emirate);
      if (street)  setVal("lm-street", street);
      // Stash exact pin coords on the modal for save
      const m = document.getElementById("servia-loc-modal");
      if (m) { m.dataset.pinLat = lat; m.dataset.pinLng = lng; }
    } catch (_) {}
  }

  function setVal(id, v) {
    const el = document.getElementById(id);
    if (el && v != null) el.value = v;
  }

  async function saveFromModal() {
    const cur = getSaved() || {};
    const m = document.getElementById("servia-loc-modal");
    // Tag: prefer the custom-input value if non-empty, else the active chip,
    // else fall back to the previously-saved tag or "Home".
    const customTag = (document.getElementById("lm-tag-custom") || {}).value || "";
    const tag = (customTag.trim() ||
                  (m && m.dataset.selectedTag) ||
                  cur.tag || "Home").slice(0, 20);
    const obj = Object.assign({}, cur, {
      tag,
      emirate: getVal("lm-emirate"),
      area: getVal("lm-area"),
      building: getVal("lm-building"),
      apartment: getVal("lm-apartment"),
      street: getVal("lm-street"),
      contact_name: getVal("lm-contact-name"),
      contact_phone: getVal("lm-contact-phone"),
      notes: getVal("lm-notes"),
      saved_at: new Date().toISOString(),
    });
    // Map pin coordinates override geolocation if user moved the marker
    if (m && m.dataset.pinLat && m.dataset.pinLng) {
      obj.lat = parseFloat(m.dataset.pinLat);
      obj.lng = parseFloat(m.dataset.pinLng);
      obj.pin_set_by_user = true;
    }
    obj.full_address = [obj.building, obj.apartment, obj.street, obj.area, obj.emirate]
      .filter(Boolean).join(", ");
    setSaved(obj);
    renderBar();
    // If logged in, sync to server saved_addresses
    try {
      const tok = localStorage.getItem("lumora.user.tok");
      if (tok && localStorage.getItem("lumora.user.type") === "customer") {
        fetch("/api/me/addresses", {
          method:"POST",
          headers:{
            "content-type":"application/json",
            "Authorization":"Bearer " + tok,
          },
          body: JSON.stringify({
            label: "Home",
            address: obj.full_address || obj.area || "",
            area: obj.area, building: obj.building, apartment: obj.apartment,
            street: obj.street, emirate: obj.emirate,
            contact_name: obj.contact_name, contact_phone: obj.contact_phone,
            notes: obj.notes,
            is_default: true,
          }),
        }).catch(()=>{});
      }
    } catch (_) {}
    const m = document.getElementById("servia-loc-modal");
    if (m) m.remove();
  }
  function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
  }

  // Public API for other scripts
  window.serviaLocation = {
    get: getSaved,
    set: setSaved,
    edit: openEditModal,
    onChange: cb => window.addEventListener("servia:location-changed", e => cb(e.detail)),
  };
})();
