"""Google Home / Google Assistant Smart Home Action integration (v1.24.15).

Servia exposes each customer's custom_sos_buttons as Google Smart Home
SCENE devices. Once linked in the Google Home app:
  · Each shortcut shows up as a tappable card titled "Servia · <label>"
  · Voice on any Nest/phone/watch: "Hey Google, run Marina flat tyre"
  · Buttons can be added to Google Home Routines

Architecture (cloud-to-cloud, the same SDK Tuya / Smart Life uses):

  Customer in Google Home app
    │
    ▼  taps "Add → Works with Google → Servia"
    │
  Google opens OAuth flow at  https://servia.ae/oauth/authorize
    │
    ▼  customer authorizes
    │
  Google calls our  POST /oauth/token  with the authorization code
    │
    ▼  we issue (access_token, refresh_token, expiry)
    │
  Google calls our  POST /api/google-home/fulfillment  with:
    intent = SYNC   → we list buttons as devices
    intent = QUERY  → state (always 'online' for scenes)
    intent = EXECUTE → ActivateScene → fire the dispatch

Three endpoints we host:
  GET  /oauth/authorize          — consent UI (HTML)
  POST /oauth/token              — token exchange (JSON)
  POST /api/google-home/fulfillment  — Google's intent dispatcher

Plus admin endpoints to verify Google Actions Console config:
  GET  /api/admin/google-home/status     — does Servia have an OAuth
       client configured? Are any Google accounts linked?
  POST /api/admin/google-home/test-sync  — simulate Google's SYNC

Tables:
  google_home_oauth_codes   (short-lived auth codes)
  google_home_oauth_tokens  (access + refresh tokens per customer)
  google_home_oauth_clients (Google's client_id + secret pair)

Setup steps for the admin (documented in admin.html):
  1. Create an Actions on Google project (Smart Home type)
  2. Configure cloud-to-cloud:
       Authorization URL = https://servia.ae/oauth/authorize
       Token URL         = https://servia.ae/oauth/token
       Client ID         = (Servia generates one — admin pastes)
       Client Secret     = (Servia generates one — admin pastes)
       Fulfillment URL   = https://servia.ae/api/google-home/fulfillment
  3. Run Google's automated test suite (Actions Console → Test)
  4. Submit for review (3-5 days)
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel

from . import db, recovery, sos_custom
from .auth import require_admin
from .auth_users import lookup_session


router = APIRouter()             # /api/google-home/*
oauth_router = APIRouter()       # /oauth/* (NO /api prefix — Google requires public URLs)


# ---------------------------------------------------------------------------
def _ensure_schema() -> None:
    with db.connect() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS google_home_oauth_clients (
                client_id     TEXT PRIMARY KEY,
                client_secret TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                last_used_at  TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS google_home_oauth_codes (
                code        TEXT PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                client_id   TEXT NOT NULL,
                redirect_uri TEXT,
                expires_at  TEXT NOT NULL,
                used_at     TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS google_home_oauth_tokens (
                access_token  TEXT PRIMARY KEY,
                refresh_token TEXT UNIQUE,
                customer_id   INTEGER NOT NULL,
                client_id     TEXT NOT NULL,
                expires_at    TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ghome_tok_cust "
                  "ON google_home_oauth_tokens(customer_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ghome_tok_refresh "
                  "ON google_home_oauth_tokens(refresh_token)")


def _now() -> str:
    return _dt.datetime.utcnow().isoformat() + "Z"


def _ensure_default_client() -> dict:
    """First-run: auto-generate a client_id + secret pair so the admin has
    something to paste into the Actions on Google console. Stored in
    google_home_oauth_clients. Idempotent."""
    _ensure_schema()
    with db.connect() as c:
        row = c.execute("SELECT * FROM google_home_oauth_clients LIMIT 1").fetchone()
        if row:
            return dict(row)
        cid = "servia-gha-" + secrets.token_urlsafe(8)
        sec = secrets.token_urlsafe(32)
        c.execute(
            "INSERT INTO google_home_oauth_clients(client_id, client_secret, created_at) "
            "VALUES(?,?,?)",
            (cid, sec, _now())
        )
        return {"client_id": cid, "client_secret": sec, "created_at": _now()}


# ---------------------------------------------------------------------------
# OAuth endpoints
# ---------------------------------------------------------------------------
@oauth_router.get("/oauth/authorize", response_class=HTMLResponse)
def oauth_authorize(
    request: Request,
    response_type: str = "code",
    client_id: str = "",
    redirect_uri: str = "",
    state: str = "",
    scope: str = "",
):
    """OAuth 2.0 authorization endpoint. Google redirects the customer's
    browser here when they tap "Link Servia" in the Google Home app.

    We show a consent page, and on Approve we 302 back to redirect_uri
    with ?code=…&state=…. Standard OAuth 2.0 authorization-code flow.
    """
    _ensure_schema()
    cli = _ensure_default_client()
    # Validate client_id
    if client_id != cli["client_id"]:
        return HTMLResponse(
            "<h1>Invalid client_id</h1>"
            "<p>The Google Home integration is misconfigured. "
            "Admin: open /admin.html → Voice integrations → copy the correct "
            "client_id into the Google Actions Console.</p>",
            status_code=400)

    # Identify the user. We require the standard Servia auth_session cookie
    # OR Bearer token in the URL (?token=…) — most users will hit this from
    # an already-authed phone browser session.
    user = _resolve_user_from_request(request)
    if not user:
        # Bounce to login → after login, back here with the same params
        nxt = "/oauth/authorize?" + str(request.url.query)
        return RedirectResponse("/login.html?next=" + nxt, status_code=302)

    # Render consent UI
    cust_name = (user.record.get("name") or "you")
    return HTMLResponse(_consent_html(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
        scope=scope,
        customer_name=cust_name,
    ))


@oauth_router.post("/oauth/authorize")
def oauth_authorize_post(
    request: Request,
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(default=""),
    scope: str = Form(default=""),
    decision: str = Form(...),     # "approve" | "deny"
):
    """User clicked Approve / Deny on the consent screen."""
    _ensure_schema()
    cli = _ensure_default_client()
    if client_id != cli["client_id"]:
        raise HTTPException(400, "invalid client_id")
    user = _resolve_user_from_request(request)
    if not user:
        raise HTTPException(401, "not authenticated")
    if decision != "approve":
        sep = "&" if "?" in redirect_uri else "?"
        return RedirectResponse(
            f"{redirect_uri}{sep}error=access_denied&state={state}", status_code=302)
    code = secrets.token_urlsafe(32)
    expires = (_dt.datetime.utcnow() + _dt.timedelta(minutes=10)).isoformat() + "Z"
    with db.connect() as c:
        c.execute(
            "INSERT INTO google_home_oauth_codes(code, customer_id, client_id, "
            "redirect_uri, expires_at) VALUES(?,?,?,?,?)",
            (code, user.user_id, client_id, redirect_uri, expires)
        )
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(f"{redirect_uri}{sep}code={code}&state={state}", status_code=302)


@oauth_router.post("/oauth/token")
async def oauth_token(request: Request):
    """OAuth 2.0 token endpoint. Google exchanges authorization codes for
    (access_token, refresh_token) here. Also handles refresh_token grants
    when access_tokens expire."""
    _ensure_schema()
    cli = _ensure_default_client()
    form = await request.form()
    grant_type = form.get("grant_type", "")
    client_id = form.get("client_id", "")
    client_secret = form.get("client_secret", "")
    if client_id != cli["client_id"] or client_secret != cli["client_secret"]:
        return JSONResponse({"error": "invalid_client"}, status_code=401)

    if grant_type == "authorization_code":
        code = form.get("code", "")
        with db.connect() as c:
            row = c.execute(
                "SELECT * FROM google_home_oauth_codes WHERE code=? "
                "AND used_at IS NULL AND expires_at > ?",
                (code, _now())
            ).fetchone()
            if not row:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            c.execute("UPDATE google_home_oauth_codes SET used_at=? WHERE code=?",
                      (_now(), code))
            access_token = "gha_at_" + secrets.token_urlsafe(28)
            refresh_token = "gha_rt_" + secrets.token_urlsafe(36)
            access_exp = (_dt.datetime.utcnow() + _dt.timedelta(hours=1)).isoformat() + "Z"
            c.execute(
                "INSERT INTO google_home_oauth_tokens(access_token, refresh_token, "
                "customer_id, client_id, expires_at, created_at) VALUES(?,?,?,?,?,?)",
                (access_token, refresh_token, row["customer_id"], client_id,
                 access_exp, _now())
            )
        return {"access_token": access_token, "refresh_token": refresh_token,
                "token_type": "Bearer", "expires_in": 3600}

    if grant_type == "refresh_token":
        rt = form.get("refresh_token", "")
        with db.connect() as c:
            row = c.execute(
                "SELECT * FROM google_home_oauth_tokens WHERE refresh_token=?",
                (rt,)
            ).fetchone()
            if not row:
                return JSONResponse({"error": "invalid_grant"}, status_code=400)
            access_token = "gha_at_" + secrets.token_urlsafe(28)
            access_exp = (_dt.datetime.utcnow() + _dt.timedelta(hours=1)).isoformat() + "Z"
            c.execute(
                "INSERT INTO google_home_oauth_tokens(access_token, refresh_token, "
                "customer_id, client_id, expires_at, created_at) VALUES(?,?,?,?,?,?)",
                (access_token, rt, row["customer_id"], row["client_id"],
                 access_exp, _now())
            )
        return {"access_token": access_token, "token_type": "Bearer", "expires_in": 3600}

    return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)


# ---------------------------------------------------------------------------
# Smart Home fulfillment — SYNC / QUERY / EXECUTE / DISCONNECT
# ---------------------------------------------------------------------------
@router.post("/api/google-home/fulfillment")
async def fulfillment(request: Request,
                       authorization: str = Header(default="")):
    """Single endpoint Google calls for every Smart Home intent."""
    _ensure_schema()
    customer_id = _customer_from_bearer(authorization)
    if not customer_id:
        return JSONResponse({"errorCode": "authFailure"}, status_code=401)

    body = await request.json()
    request_id = body.get("requestId", "")
    inputs = body.get("inputs", [])
    if not inputs:
        return {"requestId": request_id, "payload": {"errorCode": "protocolError"}}
    intent = inputs[0].get("intent", "")

    if intent == "action.devices.SYNC":
        return _intent_sync(request_id, customer_id)
    if intent == "action.devices.QUERY":
        return _intent_query(request_id, customer_id, inputs[0].get("payload", {}))
    if intent == "action.devices.EXECUTE":
        return await _intent_execute(request_id, customer_id, inputs[0].get("payload", {}),
                                      request, authorization)
    if intent == "action.devices.DISCONNECT":
        # Customer unlinked the account in Google Home app — invalidate their tokens
        with db.connect() as c:
            c.execute("DELETE FROM google_home_oauth_tokens WHERE customer_id=?",
                      (customer_id,))
        return {}
    return {"requestId": request_id, "payload": {"errorCode": "notSupported"}}


def _intent_sync(request_id: str, customer_id: int) -> dict:
    """Return every custom SOS button as a SCENE device.

    Device naming: 'Servia · <button label>' so the Google Home app shows
    them grouped under the Servia brand but with the user's own naming.
    """
    sos_custom._ensure_schema()
    with db.connect() as c:
        cust = c.execute("SELECT name, email FROM customers WHERE id=?",
                         (customer_id,)).fetchone()
        rows = c.execute(
            "SELECT * FROM custom_sos_buttons WHERE customer_id=? "
            "ORDER BY sort_order, id",
            (customer_id,)
        ).fetchall()
    devices = []
    for r in rows:
        label = r["label"] or "SOS"
        devices.append({
            "id": f"servia-sos-{r['id']}",
            "type": "action.devices.types.SCENE",
            "traits": ["action.devices.traits.Scene"],
            "name": {
                "defaultNames": ["Servia SOS Shortcut"],
                "name": f"Servia · {label}",
                "nicknames": [label, f"Servia {label}"],
            },
            "willReportState": False,
            "roomHint": "Servia",
            "deviceInfo": {
                "manufacturer": "Servia",
                "model": "SOS Shortcut",
                "hwVersion": "1.0",
                "swVersion": "1.24.15",
            },
            "attributes": {
                "sceneReversible": False,
            },
            "customData": {
                "buttonId": r["id"],
                "serviceId": r["service_id"],
                "pinRequired": bool(r["pin_required"]),
            },
        })
    return {
        "requestId": request_id,
        "payload": {
            "agentUserId": str(customer_id),
            "devices": devices,
        },
    }


def _intent_query(request_id: str, customer_id: int, payload: dict) -> dict:
    """Scenes don't have state; we just return online=True for every device."""
    devices_in = payload.get("devices", []) or []
    states = {d["id"]: {"online": True, "status": "SUCCESS"} for d in devices_in}
    return {"requestId": request_id, "payload": {"devices": states}}


async def _intent_execute(request_id: str, customer_id: int, payload: dict,
                           request: Request, authorization: str) -> dict:
    """Activate one or more scenes. For each: fire the recovery dispatch."""
    commands_in = payload.get("commands", []) or []
    results = []
    # Build a synthetic Servia auth token so _do_dispatch sees a customer.
    # We have the customer_id from the OAuth Bearer token already; reuse the
    # internal record so PIN-required buttons can still verify.
    with db.connect() as c:
        cust_row = c.execute(
            "SELECT id, phone, email, name FROM customers WHERE id=?", (customer_id,)
        ).fetchone()
    if not cust_row:
        return {"requestId": request_id, "payload": {"errorCode": "authFailure"}}
    customer_rec = dict(cust_row)

    for cmd in commands_in:
        device_ids = [d["id"] for d in cmd.get("devices", [])]
        executions = cmd.get("execution", [])
        for ex in executions:
            if ex.get("command") != "action.devices.commands.ActivateScene":
                results.append({
                    "ids": device_ids,
                    "status": "ERROR",
                    "errorCode": "actionNotAvailable",
                })
                continue
            for did in device_ids:
                # Pull the button id out of "servia-sos-<id>"
                try:
                    btn_id = int(did.replace("servia-sos-", ""))
                except Exception:
                    results.append({"ids": [did], "status": "ERROR",
                                    "errorCode": "deviceNotFound"})
                    continue
                # Check PIN-required: for Google Home, we can't prompt for PIN
                # at scene execution time. So if pin_required=True we REFUSE.
                # User must dispatch via phone/web for PIN-protected shortcuts.
                with db.connect() as c:
                    btn = c.execute(
                        "SELECT pin_required FROM custom_sos_buttons "
                        "WHERE id=? AND customer_id=?",
                        (btn_id, customer_id)
                    ).fetchone()
                if not btn:
                    results.append({"ids": [did], "status": "ERROR",
                                    "errorCode": "deviceNotFound"})
                    continue
                if btn["pin_required"]:
                    results.append({"ids": [did], "status": "ERROR",
                                    "errorCode": "pinNeeded"})
                    continue
                try:
                    sos_custom._do_dispatch(
                        btn_id, customer_id, customer_rec, "",
                        request, authorization, source="google_home"
                    )
                    results.append({"ids": [did], "status": "SUCCESS"})
                except HTTPException as e:
                    results.append({"ids": [did], "status": "ERROR",
                                    "errorCode": "deviceTurnedOff",
                                    "debugString": e.detail})
                except Exception as e:
                    results.append({"ids": [did], "status": "ERROR",
                                    "errorCode": "deviceTurnedOff",
                                    "debugString": str(e)})
    return {"requestId": request_id, "payload": {"commands": results}}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_user_from_request(request: Request):
    """Find the Servia customer behind this request — cookie session or
    ?token= URL param (so Google's OAuth redirect can carry through)."""
    # First: Bearer in URL
    tok = request.query_params.get("token") or ""
    if not tok:
        # Cookie or session
        tok = request.cookies.get("servia_token", "") or ""
    if not tok:
        # Try Authorization header (for testing)
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            tok = auth[7:].strip()
    if not tok:
        return None
    return lookup_session(tok)


def _customer_from_bearer(auth: str) -> int | None:
    """Resolve the Google-issued OAuth Bearer back to a Servia customer_id."""
    if not auth.lower().startswith("bearer "):
        return None
    tok = auth[7:].strip()
    if not tok.startswith("gha_at_"):
        return None
    with db.connect() as c:
        row = c.execute(
            "SELECT customer_id, expires_at FROM google_home_oauth_tokens "
            "WHERE access_token=?", (tok,)
        ).fetchone()
    if not row or row["expires_at"] < _now():
        return None
    return int(row["customer_id"])


# ---------------------------------------------------------------------------
# Admin endpoints (+ docs)
# ---------------------------------------------------------------------------
@router.get("/api/admin/google-home/status",
             dependencies=[Depends(require_admin)])
def admin_status():
    _ensure_schema()
    cli = _ensure_default_client()
    with db.connect() as c:
        n_codes = c.execute(
            "SELECT COUNT(*) AS n FROM google_home_oauth_codes WHERE used_at IS NOT NULL"
        ).fetchone()["n"]
        n_tokens = c.execute(
            "SELECT COUNT(DISTINCT customer_id) AS n FROM google_home_oauth_tokens"
        ).fetchone()["n"]
        n_buttons = c.execute(
            "SELECT COUNT(*) AS n FROM custom_sos_buttons"
        ).fetchone()["n"]
    return {
        "client_id": cli["client_id"],
        "client_secret": cli["client_secret"],
        "fulfillment_url": "https://servia.ae/api/google-home/fulfillment",
        "authorization_url": "https://servia.ae/oauth/authorize",
        "token_url": "https://servia.ae/oauth/token",
        "linked_customers": n_tokens,
        "auth_codes_used": n_codes,
        "exposed_devices_total": n_buttons,
    }


@router.post("/api/admin/google-home/test-sync",
              dependencies=[Depends(require_admin)])
async def admin_test_sync(payload: dict):
    """Simulate Google's SYNC intent for a given customer_id, useful for
    sanity-checking before submitting to Actions on Google for review."""
    _ensure_schema()
    customer_id = int(payload.get("customer_id") or 0)
    if not customer_id:
        raise HTTPException(400, "customer_id required")
    return _intent_sync("admin-test", customer_id)


# ---------------------------------------------------------------------------
def _consent_html(client_id, redirect_uri, state, scope, customer_name) -> str:
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Allow Google Home access · Servia</title>
<style>
  body{{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#F8FAFC;color:#0F172A}}
  .wrap{{max-width:520px;margin:0 auto;padding:24px 18px}}
  header{{text-align:center;margin-bottom:18px}}
  header img{{width:72px;height:72px;border-radius:18px}}
  h1{{margin:14px 0 4px;font-size:22px}}
  .card{{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:18px;margin-bottom:14px}}
  .perm{{display:flex;gap:10px;align-items:flex-start;padding:8px 0}}
  .perm .ic{{font-size:22px;flex-shrink:0}}
  .perm b{{display:block;font-size:13.5px}}
  .perm small{{color:#64748B;font-size:12px}}
  .row{{display:flex;gap:8px;margin-top:14px}}
  button{{flex:1;padding:13px;border:0;border-radius:10px;font-weight:800;font-size:14px;cursor:pointer}}
  .approve{{background:#0F766E;color:#fff}}
  .deny{{background:#fff;color:#475569;border:1px solid #CBD5E1}}
  small.foot{{display:block;text-align:center;color:#64748B;margin-top:14px}}
</style></head><body>
<div class="wrap">
  <header>
    <img src="/brand/servia-icon-512x512.png" alt="Servia">
    <h1>Allow Google Home<br>to control your Servia shortcuts?</h1>
  </header>
  <div class="card">
    <div class="perm"><span class="ic">👤</span><div><b>Account: {customer_name}</b><small>You'll be controlling these shortcuts.</small></div></div>
    <div class="perm"><span class="ic">🆘</span><div><b>See your custom SOS shortcuts</b><small>Names, emojis, and types only — no GPS, no addresses.</small></div></div>
    <div class="perm"><span class="ic">▶️</span><div><b>Trigger a shortcut when you ask</b><small>"Hey Google, run Marina flat tyre" → fires the recovery dispatch.</small></div></div>
    <div class="perm"><span class="ic">🔒</span><div><b>PIN-required shortcuts are blocked</b><small>For safety, voice/Google Home can't fire shortcuts that need your PIN. Use Servia app for those.</small></div></div>
  </div>
  <form method="POST" action="/oauth/authorize" autocomplete="off">
    <input type="hidden" name="client_id" value="{client_id}">
    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
    <input type="hidden" name="state" value="{state}">
    <input type="hidden" name="scope" value="{scope}">
    <div class="row">
      <button type="submit" name="decision" value="deny" class="deny">Deny</button>
      <button type="submit" name="decision" value="approve" class="approve">Allow</button>
    </div>
  </form>
  <small class="foot">You can disconnect any time from the Google Home app → Servia.</small>
</div>
</body></html>"""
