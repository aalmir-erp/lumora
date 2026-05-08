"""Admin panel routes — auth, dashboard, settings, KB editor, orders.

Mounted at /admin. The first-time setup flow uses ADMIN_BOOTSTRAP_TOKEN
(env var) to set the initial admin password without anyone being
locked out.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import auth, db, kb, orders, settings_store


router = APIRouter(prefix="/admin", tags=["admin"])

_templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=_templates_dir)


def render(request: Request, name: str, context: dict[str, Any] | None = None, status: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context or {}, status_code=status)


def _check(request: Request) -> None:
    if not auth.is_logged_in(request):
        raise HTTPException(status_code=302, headers={"Location": "/admin/login"})


def _render_error(request: Request, template: str, msg: str, **extra) -> HTMLResponse:
    ctx: dict[str, Any] = {"error": msg}
    ctx.update(extra)
    return render(request, template, ctx, status=400)


# ---------- setup / login / logout ----------

@router.get("/setup", response_model=None)
async def setup_form(request: Request):
    if auth.is_password_set():
        return RedirectResponse("/admin/login", status_code=302)
    return render(request, "setup.html", {"needs_bootstrap": bool(auth.bootstrap_token())})


@router.post("/setup", response_model=None)
async def setup_submit(
    request: Request,
    bootstrap_token: str = Form(""),
    password: str = Form(...),
    confirm: str = Form(...),
):
    if auth.is_password_set():
        return RedirectResponse("/admin/login", status_code=302)
    expected = auth.bootstrap_token()
    if expected and bootstrap_token != expected:
        return _render_error(request, "setup.html", "Bootstrap token doesn't match.", needs_bootstrap=True)
    if password != confirm:
        return _render_error(request, "setup.html", "Passwords don't match.", needs_bootstrap=bool(expected))
    try:
        auth.set_password(password)
    except ValueError as e:
        return _render_error(request, "setup.html", str(e), needs_bootstrap=bool(expected))
    auth.login(request)
    return RedirectResponse("/admin", status_code=302)


@router.get("/login", response_model=None)
async def login_form(request: Request):
    if not auth.is_password_set():
        return RedirectResponse("/admin/setup", status_code=302)
    return render(request, "login.html")


@router.post("/login", response_model=None)
async def login_submit(request: Request, password: str = Form(...)):
    if auth.check_login(password):
        auth.login(request)
        return RedirectResponse("/admin", status_code=302)
    return _render_error(request, "login.html", "Wrong password.")


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    auth.logout(request)
    return RedirectResponse("/admin/login", status_code=302)


# ---------- dashboard ----------

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    _check(request)
    settings_rows = settings_store.all_for_admin()
    counts = _counts()
    health = _health(settings_rows)
    return render(
        request,
        "dashboard.html",
        {"settings_rows": settings_rows, "counts": counts, "health": health},
    )


# ---------- settings ----------

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    _check(request)
    return render(request, "settings.html", {"rows": settings_store.all_for_admin()})


@router.post("/settings")
async def settings_save(request: Request) -> RedirectResponse:
    _check(request)
    form = await request.form()
    saved = 0
    for key, _, _, _ in settings_store.EDITABLE_KEYS:
        val = (form.get(key) or "").strip()
        if val:
            settings_store.set_value(key, val)
            saved += 1
    return RedirectResponse(f"/admin/settings?saved={saved}", status_code=302)


@router.get("/setup-guide", response_class=HTMLResponse)
async def setup_guide(request: Request) -> HTMLResponse:
    _check(request)
    return render(request, "setup_guide.html")


# ---------- KB editor ----------

@router.get("/kb", response_class=HTMLResponse)
async def kb_page(request: Request) -> HTMLResponse:
    _check(request)
    return render(request, "kb.html", {"blocks": kb.list_blocks()})


@router.post("/kb/{slug}")
async def kb_save(
    request: Request,
    slug: str,
    title: str = Form(...),
    content: str = Form(...),
) -> RedirectResponse:
    _check(request)
    kb.save_block(slug, title.strip(), content.strip())
    return RedirectResponse("/admin/kb", status_code=302)


@router.post("/kb/{slug}/reset")
async def kb_reset(request: Request, slug: str) -> RedirectResponse:
    _check(request)
    kb.reset_block(slug)
    return RedirectResponse("/admin/kb", status_code=302)


# ---------- orders ----------

@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request) -> HTMLResponse:
    _check(request)
    status = request.query_params.get("status") or None
    rows = orders.list_recent(limit=200, status=status)
    return render(request, "orders.html", {"orders": rows, "status_filter": status})


@router.post("/orders/{order_id}/status")
async def orders_update_status(
    request: Request, order_id: int, status: str = Form(...)
) -> RedirectResponse:
    _check(request)
    if status not in {"new", "contacted", "quoted", "closed", "lost"}:
        raise HTTPException(status_code=400, detail="invalid status")
    orders.update_status(order_id, status)
    return RedirectResponse("/admin/orders", status_code=302)


# ---------- conversations ----------

@router.get("/conversations", response_class=HTMLResponse)
async def conversations_page(request: Request) -> HTMLResponse:
    _check(request)
    with db.connect() as c:
        groups = c.execute(
            """SELECT wa_id, COUNT(*) AS msgs, MAX(created_at) AS last_at
               FROM conversations GROUP BY wa_id ORDER BY last_at DESC LIMIT 50"""
        ).fetchall()
    return render(request, "conversations.html", {"groups": [dict(r) for r in groups]})


@router.get("/conversations/{wa_id}", response_class=HTMLResponse)
async def conversation_view(request: Request, wa_id: str) -> HTMLResponse:
    _check(request)
    with db.connect() as c:
        rows = c.execute(
            "SELECT role, content, created_at FROM conversations WHERE wa_id = ? ORDER BY id ASC",
            (wa_id,),
        ).fetchall()
    return render(
        request,
        "conversation_view.html",
        {"wa_id": wa_id, "messages": [dict(r) for r in rows]},
    )


# ---------- helpers ----------

def _counts() -> dict[str, int]:
    with db.connect() as c:
        orders_total = c.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"]
        orders_new = c.execute(
            "SELECT COUNT(*) AS n FROM orders WHERE status = 'new'"
        ).fetchone()["n"]
        convs = c.execute(
            "SELECT COUNT(DISTINCT wa_id) AS n FROM conversations"
        ).fetchone()["n"]
    return {"orders_total": orders_total, "orders_new": orders_new, "conversations": convs}


def _health(settings_rows: list[dict]) -> dict[str, bool]:
    by_key = {r["key"]: r for r in settings_rows}

    def has(k: str) -> bool:
        return by_key.get(k, {}).get("has_value", False)

    provider = settings_store.ai_provider()
    ai_ok = (
        (provider == "anthropic" and has("ANTHROPIC_API_KEY"))
        or (provider == "openai" and has("OPENAI_API_KEY"))
    )
    return {
        "meta_token": has("META_ACCESS_TOKEN"),
        "meta_phone": has("META_PHONE_NUMBER_ID"),
        "meta_secret": has("META_APP_SECRET"),
        "meta_verify": has("META_VERIFY_TOKEN"),
        "ai_ok": ai_ok,
        "bot_enabled": settings_store.bot_enabled(),
    }
