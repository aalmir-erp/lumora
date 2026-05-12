/* v1.24.143 — Frontend helper: fetches /api/brand/contact and replaces
 * every element with `data-bc-*` attributes with the current value.
 *
 * Usage in any HTML page:
 *   <a href="" data-bc-href="tel">+971 4 000 0000</a>
 *   <a href="" data-bc-href="whatsapp" data-bc-text>WhatsApp us</a>
 *   <a href="" data-bc-href="mailto">support@servia.ae</a>
 *   <span data-bc-phone></span>
 *   <span data-bc-email></span>
 *   <span data-bc-whatsapp></span>
 *
 * Include with: <script src="/brand-contact.js" defer></script>
 */
(function(){
  if (window.__bc_loaded) return;
  window.__bc_loaded = true;

  fetch("/api/brand/contact", { credentials: "same-origin" })
    .then(r => r.json())
    .then(d => {
      if (!d || !d.ok) return;

      // text replacements
      const map = {
        "data-bc-phone":    d.contact_phone || "",
        "data-bc-email":    d.contact_email || "",
        "data-bc-whatsapp": d.contact_whatsapp || d.contact_phone || "",
        "data-bc-brand":    d.brand_name || "Servia",
        "data-bc-address":  d.company_address || "",
      };
      for (const attr in map) {
        document.querySelectorAll("[" + attr + "]").forEach(el => {
          // If element has text content (other than what's already a number/email),
          // replace it. Otherwise just set textContent.
          el.textContent = map[attr];
        });
      }

      // href replacements
      document.querySelectorAll("[data-bc-href]").forEach(el => {
        const kind = el.getAttribute("data-bc-href");
        if (kind === "tel" && d.tel_url)               el.setAttribute("href", d.tel_url);
        else if (kind === "mailto" && d.mailto_url)    el.setAttribute("href", d.mailto_url);
        else if (kind === "whatsapp" && d.whatsapp_url) el.setAttribute("href", d.whatsapp_url);
      });

      // Update WhatsApp widget defaults if present
      if (window.LUMORA_BRAND_CONTACT) {
        Object.assign(window.LUMORA_BRAND_CONTACT, d);
      } else {
        window.LUMORA_BRAND_CONTACT = d;
      }
      window.dispatchEvent(new CustomEvent("bc-loaded", { detail: d }));
    })
    .catch(() => {/* silent */});
})();
