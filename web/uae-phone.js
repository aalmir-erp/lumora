/* Servia UAE phone validator — shared across every form on the site.
 *
 * UAE mobile rules:
 *   - Country code: +971 (or 00971 / 971)
 *   - National prefix when no country code: 0
 *   - Mobile starts with 5 followed by carrier digit 0/2/4/5/6/8/9
 *   - 7 trailing digits
 * Examples that count as valid:
 *     +971501234567   (full international)
 *      971501234567
 *      0501234567     (local with leading 0)
 *       501234567     (no leading 0 — we add +971)
 *
 * Normalises every input to E.164 form: +971XXXXXXXXX
 */
(function () {
  const HINT = "UAE mobile number only — must start with +971 or 05.";
  const ERR = {
    en: "Please enter a valid UAE mobile number — starts with +971 or 05 (e.g. +971501234567).",
    ar: "يرجى إدخال رقم هاتف متحرك إماراتي صالح — يبدأ بـ +971 أو 05 (مثال: +971501234567).",
  };

  // Strip everything except digits and a leading +
  function _clean(raw) {
    const s = (raw || "").trim().replace(/[\s\-()]/g, "");
    return s;
  }
  // Returns null if invalid, otherwise the canonical +971XXXXXXXXX form
  function normalizeUAEPhone(raw) {
    let s = _clean(raw);
    if (!s) return null;
    // 00971... → +971...
    if (s.startsWith("00971")) s = "+" + s.slice(2);
    // 971... → +971...
    if (s.startsWith("971")) s = "+" + s;
    // 05X... → +9715X...
    if (s.startsWith("05")) s = "+971" + s.slice(1);
    // 5X... (no leading 0 or country code) → +9715X...
    if (/^5[0245689]\d{7}$/.test(s)) s = "+971" + s;
    // Now validate strict E.164: +9715[0245689]XXXXXXX
    if (/^\+9715[0245689]\d{7}$/.test(s)) return s;
    return null;
  }
  function isValidUAEPhone(raw) {
    return normalizeUAEPhone(raw) !== null;
  }

  // Wire one input field with: inline hint, error styling on blur, and
  // auto-normalisation on submit-time read. Returns a getter that forms
  // call before submitting — returns the canonical phone or shows the
  // error and returns null.
  function bindUAEPhone(input, opts) {
    if (!input || input.dataset.uaeBound === "1") return;
    input.dataset.uaeBound = "1";
    opts = opts || {};

    // Standardise input attributes for mobile keyboards
    input.type = input.type || "tel";
    input.setAttribute("inputmode", "tel");
    input.setAttribute("autocomplete", "tel");
    if (!input.placeholder || input.placeholder === "") {
      input.placeholder = "+971501234567";
    }

    // Insert a small hint right after the input if the form doesn't
    // already have one (skip when caller passes silentHint=true)
    if (!opts.silentHint) {
      let hint = input.parentNode.querySelector(".uae-phone-hint");
      if (!hint) {
        hint = document.createElement("div");
        hint.className = "uae-phone-hint";
        hint.style.cssText = "font-size:11px;color:#64748B;margin-top:3px;line-height:1.4";
        hint.textContent = "🇦🇪 " + HINT;
        input.parentNode.insertBefore(hint, input.nextSibling);
      }
    }

    // Live validation — green border when valid, red when not (on blur only,
    // so we don't shout while the user is still typing)
    function paintState() {
      const v = input.value.trim();
      if (!v) { input.style.borderColor = ""; return; }
      input.style.borderColor = isValidUAEPhone(v) ? "#15803D" : "#B91C1C";
    }
    input.addEventListener("blur", paintState);

    // Re-flow the value into canonical form on blur if valid
    input.addEventListener("blur", () => {
      const norm = normalizeUAEPhone(input.value);
      if (norm) input.value = norm;
    });
  }

  // Helper for forms: validate + alert + return canonical, OR return null
  function readUAEPhoneOrAlert(input, lang) {
    const norm = normalizeUAEPhone((input || {}).value);
    if (!norm) {
      const lng = (lang || (window.lumoraLang ? lumoraLang() : "en")).slice(0, 2);
      const msg = ERR[lng] || ERR.en;
      alert(msg);
      try { input.focus(); } catch (_) {}
      return null;
    }
    if (input) input.value = norm;
    return norm;
  }

  window.UAEPhone = {
    isValid: isValidUAEPhone,
    normalize: normalizeUAEPhone,
    bind: bindUAEPhone,
    readOrAlert: readUAEPhoneOrAlert,
    HINT, ERR,
  };
})();
