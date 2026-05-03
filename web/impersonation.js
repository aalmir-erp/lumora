/* Lumora impersonation banner — shown when admin is "viewing as" another user.
 *
 * Storage flags written by /admin.html when admin clicks "View as":
 *   lumora.user.tok               — the impersonated session token
 *   lumora.user.type              — 'customer' or 'vendor'
 *   lumora.user.impersonated      — '1' marker
 *   lumora.user.impersonated_name — display name
 *   lumora.admin.original_tok     — admin token to restore
 */
(function () {
  if (localStorage.getItem("lumora.user.impersonated") !== "1") return;
  const name = localStorage.getItem("lumora.user.impersonated_name") || "user";
  const type = localStorage.getItem("lumora.user.type") || "user";

  const bar = document.createElement("div");
  bar.style.cssText =
    "position:sticky;top:0;z-index:99999;background:linear-gradient(90deg,#7C2D12,#9A3412);" +
    "color:#fff;padding:10px 16px;display:flex;align-items:center;justify-content:center;" +
    "gap:14px;font-size:13px;font-weight:600;box-shadow:0 4px 14px rgba(0,0,0,.18);" +
    "flex-wrap:wrap;text-align:center";
  bar.innerHTML =
    '<span>🛡 You are viewing as <b>' + (type === "vendor" ? "vendor" : "customer") + ' ' +
    name.replace(/[<>&"]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"}[c])) + '</b>. ' +
    'Anything you click happens in their account.</span>' +
    '<button id="lumora-revert-admin" style="background:#fff;color:#9A3412;border:0;' +
    'padding:6px 14px;border-radius:999px;font-weight:700;cursor:pointer;font-size:12px">' +
    '↩ Return to admin</button>';
  document.body.insertBefore(bar, document.body.firstChild);

  document.getElementById("lumora-revert-admin").onclick = () => {
    const adminTok = localStorage.getItem("lumora.admin.original_tok");
    // Revoke the impersonated session server-side (best effort)
    const userTok = localStorage.getItem("lumora.user.tok");
    if (userTok) {
      fetch("/api/auth/logout", {
        method: "POST",
        headers: { "content-type": "application/json", authorization: "Bearer " + userTok }
      }).catch(()=>{});
    }
    // Clear impersonation flags
    ["lumora.user.tok","lumora.user.type","lumora.user.impersonated",
     "lumora.user.impersonated_name","lumora.admin.original_tok"].forEach(k => localStorage.removeItem(k));
    if (adminTok) localStorage.setItem("lumora.admin.tok", adminTok);
    location.replace("/admin.html");
  };
})();
