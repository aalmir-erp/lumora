/* Lumora dynamic intake form renderer.
 *
 * Reads the per-service `intake` array from /api/services and renders
 * service-appropriate inputs only. NEVER asks bedrooms for car_wash etc.
 *
 * Each intake token can be:
 *   "bedrooms"                                      → number input
 *   "pool_size_sqm"                                 → number input (anything ending in _sqm/_sqft/_count/_kg)
 *   "frequency (one-time/weekly/biweekly)"          → select with the options
 *   "ac_type (split/window/ducted/central)"         → select
 *   "preferred_date"                                → date input
 *   "time_slot"                                     → time select
 *   "emirate"                                       → select with UAE emirates
 *   "property_address" / "villa_address" / "..."    → textarea
 *   anything else                                   → text input
 *
 * Public API:
 *   LumoraIntake.render(serviceId, { mount }) — renders into element with that id
 *   LumoraIntake.values()                     — returns {field: value} object
 *   LumoraIntake.summary()                    — returns human-readable string
 */
(function () {
  const EMIRATES = ["Dubai","Sharjah","Ajman","Abu Dhabi","Ras Al Khaimah","Umm Al Quwain","Fujairah"];
  const TIME_SLOTS = ["08:00","10:00","12:00","14:00","16:00","18:00"];
  const NUMBER_HINTS = /(_count|_sqft|_sqm|_kg|_panels?|_rooms?|_floors?|_units?|hours?_needed|children_count|bedrooms|bathrooms|floors)$/i;

  let rendered = [];   // list of { key, type, el, label }
  let currentSvc = null;

  function humanize(token) {
    // strip "(opt/opt/opt)" suffix and replace _ with space, capitalize
    const base = token.replace(/\s*\([^)]*\)\s*$/, "").trim();
    return base.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  }

  function parseOptions(token) {
    const m = token.match(/\(([^)]+)\)/);
    if (!m) return null;
    return m[1].split("/").map(s => s.trim()).filter(Boolean);
  }

  function fieldType(token) {
    const key = token.split(/\s/)[0].trim();
    if (parseOptions(token)) return "select";
    if (/^preferred_date$|_date$/.test(key)) return "date";
    if (/^time_slot$/.test(key)) return "timeslot";
    if (/^emirate$/.test(key)) return "emirate";
    if (/address|description/i.test(key)) return "textarea";
    if (NUMBER_HINTS.test(key)) return "number";
    return "text";
  }

  function el(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    for (const k of kids) e.appendChild(typeof k === "string" ? document.createTextNode(k) : k);
    return e;
  }

  function renderField(token) {
    const key = token.split(/\s/)[0].trim();
    const type = fieldType(token);
    const label = humanize(token);
    const id = "intake_" + key.replace(/[^a-z0-9]/gi, "_");

    const wrap = el("div", { class: "intake-field" });
    const lab = el("label", { for: id }, label);
    wrap.appendChild(lab);

    let input;
    if (type === "select") {
      input = el("select", { id });
      input.appendChild(el("option", { value: "" }, "Choose…"));
      for (const o of parseOptions(token)) input.appendChild(el("option", { value: o }, o.replace(/_/g, " ")));
    } else if (type === "emirate") {
      input = el("select", { id });
      input.appendChild(el("option", { value: "" }, "Choose emirate…"));
      for (const o of EMIRATES) input.appendChild(el("option", { value: o }, o));
    } else if (type === "timeslot") {
      input = el("select", { id });
      input.appendChild(el("option", { value: "" }, "Choose time…"));
      for (const o of TIME_SLOTS) input.appendChild(el("option", { value: o }, o));
    } else if (type === "date") {
      input = el("input", { id, type: "date" });
      const today = new Date(); today.setDate(today.getDate());
      input.min = today.toISOString().slice(0, 10);
    } else if (type === "number") {
      input = el("input", { id, type: "number", min: "0", inputmode: "numeric" });
    } else if (type === "textarea") {
      input = el("textarea", { id, rows: "2", placeholder: "e.g. tower / villa, apt no, street, area" });
    } else {
      input = el("input", { id, type: "text" });
    }
    wrap.appendChild(input);
    return { wrap, input, key, label, type };
  }

  async function fetchService(id) {
    const r = await fetch("/api/services").then(r => r.json());
    return (r.services || []).find(s => s.id === id);
  }

  async function render(serviceId, opts) {
    const mount = typeof opts.mount === "string" ? document.getElementById(opts.mount) : opts.mount;
    if (!mount) { console.warn("[intake] mount not found"); return; }
    mount.innerHTML = "";
    rendered = [];

    const svc = await fetchService(serviceId);
    currentSvc = svc;
    if (!svc) {
      mount.innerHTML = '<p style="color:var(--muted)">Pick a service first.</p>';
      return;
    }

    // Header — clarifies which questions belong to which service
    const head = el("div", { class: "intake-head" },
      el("strong", {}, `For ${svc.name}, we just need:`));
    mount.appendChild(head);

    const grid = el("div", { class: "intake-grid" });
    const intake = svc.intake || ["preferred_date","time_slot","emirate","property_address"];
    for (const tok of intake) {
      const f = renderField(tok);
      grid.appendChild(f.wrap);
      rendered.push(f);
    }
    mount.appendChild(grid);

    // Auto-emit a "values changed" event so callers can react (e.g., live quote)
    grid.addEventListener("change", () => {
      mount.dispatchEvent(new CustomEvent("intake:change", { detail: values() }));
    });
  }

  function values() {
    const out = {};
    for (const f of rendered) {
      const v = f.input.value;
      if (v !== "" && v !== null && v !== undefined) out[f.key] = v;
    }
    return out;
  }

  function summary() {
    const parts = [];
    for (const f of rendered) {
      const v = f.input.value;
      if (v) parts.push(`${f.label}: ${v}`);
    }
    return parts.join(", ");
  }

  function service() { return currentSvc; }

  // Strip [[choices: ...]] marker from any bot text and parse into clickable choices.
  function parseBotText(text) {
    const choices = [];
    const cleaned = (text || "").replace(/\[\[\s*choices?\s*:\s*([^\]]+)\]\]/gi, (_, body) => {
      body.split(/\s*;\s*/).forEach(pair => {
        const m = pair.match(/^\s*(.+?)\s*=\s*(.+?)\s*$/);
        if (m) choices.push({ label: m[1], send: m[2] });
        else if (pair.trim()) choices.push({ label: pair.trim(), send: pair.trim() });
      });
      return "";
    }).replace(/\n{3,}/g, "\n\n").trim();
    return { text: cleaned, choices };
  }

  // Apply a chosen value to the best matching intake field (auto-fill from chips).
  function applyChoiceToBestField(send) {
    if (!rendered.length) return false;
    for (const f of rendered) {
      if (f.input.tagName === "SELECT") {
        for (const opt of f.input.options) {
          if (opt.value && opt.value.toLowerCase() === send.toLowerCase()) {
            f.input.value = opt.value;
            f.input.dispatchEvent(new Event("change", { bubbles: true }));
            return true;
          }
        }
      }
    }
    if (/^\d+(\.\d+)?$/.test(send)) {
      for (const f of rendered) {
        if (f.input.type === "number" && !f.input.value) {
          f.input.value = send;
          f.input.dispatchEvent(new Event("change", { bubbles: true }));
          return true;
        }
      }
    }
    return false;
  }

  // Attach a small style block once
  if (!document.getElementById("intake-style")) {
    const style = document.createElement("style");
    style.id = "intake-style";
    style.textContent = `
      .intake-head { margin: 0 0 12px; padding: 12px 14px;
        background: color-mix(in srgb, var(--primary) 8%, var(--surface));
        border-left: 3px solid var(--primary); border-radius: 8px; font-size: 14px; }
      .intake-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
      .intake-field { display: flex; flex-direction: column; gap: 4px; }
      .intake-field label { font-size: 13px; font-weight: 600; color: var(--text); }
      .intake-field input, .intake-field select, .intake-field textarea {
        padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px;
        background: var(--bg); color: var(--text); font: inherit; width: 100%;
      }
      .intake-field input:focus, .intake-field select:focus, .intake-field textarea:focus {
        outline: 2px solid color-mix(in srgb, var(--primary) 35%, transparent);
        border-color: var(--primary);
      }
    `;
    document.head.appendChild(style);
  }

  window.LumoraIntake = { render, values, summary, service, parseBotText, applyChoiceToBestField };
})();
