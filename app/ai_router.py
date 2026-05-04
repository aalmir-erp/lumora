"""Multi-provider AI router.

Admin pastes API keys for OpenAI / Anthropic / Google / Mistral / DeepSeek /
Groq / Together / OpenRouter, picks a default model per persona (customer /
admin / vendor / blog / video) and can run an 'arena' that fans one prompt
out to N selected models in parallel and returns all responses.

All keys + defaults persist via db.cfg. Provider calls are stateless and
simple HTTP — no SDK lock-in.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from . import db
from .auth import require_admin

router = APIRouter(prefix="/api/admin/ai", tags=["admin-ai"],
                   dependencies=[Depends(require_admin)])

# ---------- catalogue ----------
# Curated model list per provider — including free/cheap tiers. Updated 2026.
MODEL_CATALOG = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "key_env": "ANTHROPIC_API_KEY",
        "get_key_url": "https://console.anthropic.com/settings/keys",
        "pricing_url": "https://www.anthropic.com/pricing",
        "free_tier": "No free tier — $5 credit on signup",
        "models": [
            {"id": "claude-opus-4-7",       "tier": "premium", "label": "Claude Opus 4.7", "price_per_1m": "$15 in / $75 out"},
            {"id": "claude-sonnet-4-6",     "tier": "balanced","label": "Claude Sonnet 4.6", "price_per_1m": "$3 in / $15 out"},
            {"id": "claude-haiku-4-5-20251001", "tier": "fast", "label": "Claude Haiku 4.5", "price_per_1m": "$0.80 in / $4 out"},
        ],
    },
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "key_env": "OPENAI_API_KEY",
        "get_key_url": "https://platform.openai.com/api-keys",
        "pricing_url": "https://openai.com/api/pricing/",
        "free_tier": "No free tier — pay as you go",
        "models": [
            {"id": "gpt-4o",      "tier": "premium",  "label": "GPT-4o", "price_per_1m": "$2.50 in / $10 out"},
            {"id": "gpt-4o-mini", "tier": "fast",     "label": "GPT-4o mini", "price_per_1m": "$0.15 in / $0.60 out"},
            {"id": "o1-mini",     "tier": "premium",  "label": "o1-mini (reasoning)", "price_per_1m": "$3 in / $12 out"},
        ],
    },
    "google": {
        "label": "Google (Gemini)",
        "key_env": "GOOGLE_API_KEY",
        "get_key_url": "https://aistudio.google.com/app/apikey",
        "pricing_url": "https://ai.google.dev/pricing",
        "free_tier": "FREE up to 15 req/min · 1.5K req/day for Flash",
        "models": [
            {"id": "gemini-1.5-pro",   "tier": "premium", "label": "Gemini 1.5 Pro", "price_per_1m": "$1.25 in / $5 out"},
            {"id": "gemini-1.5-flash", "tier": "fast",    "label": "Gemini 1.5 Flash (FREE tier)", "price_per_1m": "FREE up to 1.5K req/day"},
        ],
    },
    "mistral": {
        "label": "Mistral",
        "key_env": "MISTRAL_API_KEY",
        "get_key_url": "https://console.mistral.ai/api-keys",
        "pricing_url": "https://mistral.ai/products/la-plateforme#pricing",
        "free_tier": "Free dev tier (rate-limited)",
        "models": [
            {"id": "mistral-large-latest", "tier": "premium",  "label": "Mistral Large", "price_per_1m": "$2 in / $6 out"},
            {"id": "mistral-small-latest", "tier": "balanced", "label": "Mistral Small", "price_per_1m": "$0.20 in / $0.60 out"},
            {"id": "open-mistral-7b",      "tier": "free",     "label": "Open Mistral 7B (cheap)", "price_per_1m": "$0.25 in / $0.25 out"},
        ],
    },
    "deepseek": {
        "label": "DeepSeek (cheap + capable)",
        "key_env": "DEEPSEEK_API_KEY",
        "get_key_url": "https://platform.deepseek.com/api_keys",
        "pricing_url": "https://api-docs.deepseek.com/quick_start/pricing",
        "free_tier": "$5 free credit on signup",
        "models": [
            {"id": "deepseek-chat",     "tier": "balanced", "label": "DeepSeek Chat", "price_per_1m": "$0.27 in / $1.10 out"},
            {"id": "deepseek-reasoner", "tier": "premium",  "label": "DeepSeek Reasoner", "price_per_1m": "$0.55 in / $2.19 out"},
        ],
    },
    "groq": {
        "label": "Groq (fast inference, free tier)",
        "key_env": "GROQ_API_KEY",
        "get_key_url": "https://console.groq.com/keys",
        "pricing_url": "https://console.groq.com/pricing",
        "free_tier": "FREE tier — 30 req/min, no card required",
        "models": [
            {"id": "llama-3.3-70b-versatile",  "tier": "free", "label": "Llama 3.3 70B (FREE)", "price_per_1m": "FREE"},
            {"id": "mixtral-8x7b-32768",       "tier": "free", "label": "Mixtral 8x7B (FREE)", "price_per_1m": "FREE"},
            {"id": "gemma2-9b-it",             "tier": "free", "label": "Gemma 2 9B (FREE)", "price_per_1m": "FREE"},
        ],
    },
    "together": {
        "label": "Together AI (open models)",
        "key_env": "TOGETHER_API_KEY",
        "get_key_url": "https://api.together.xyz/settings/api-keys",
        "pricing_url": "https://www.together.ai/pricing",
        "free_tier": "$1 free credit on signup",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "tier": "free",     "label": "Llama 3.3 70B Turbo", "price_per_1m": "$0.88"},
            {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo",         "tier": "balanced", "label": "Qwen 2.5 72B", "price_per_1m": "$1.20"},
        ],
    },
    "openrouter": {
        "label": "OpenRouter (any model, one key)",
        "key_env": "OPENROUTER_API_KEY",
        "get_key_url": "https://openrouter.ai/keys",
        "pricing_url": "https://openrouter.ai/models",
        "free_tier": "FREE tier on selected models (rate-limited)",
        "models": [
            {"id": "anthropic/claude-opus-4",     "tier": "premium", "label": "Claude Opus 4 (via OR)", "price_per_1m": "$15 in / $75 out"},
            {"id": "openai/gpt-4o",               "tier": "premium", "label": "GPT-4o (via OR)", "price_per_1m": "$2.50 in / $10 out"},
            {"id": "google/gemini-pro-1.5",       "tier": "premium", "label": "Gemini 1.5 Pro (via OR)", "price_per_1m": "$1.25 in / $5 out"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "tier": "free", "label": "Llama 3.3 70B (FREE)", "price_per_1m": "FREE"},
            {"id": "deepseek/deepseek-chat",      "tier": "balanced","label": "DeepSeek Chat (via OR)", "price_per_1m": "$0.27 in / $1.10 out"},
        ],
    },
}


def _load_cfg() -> dict:
    cur = db.cfg_get("ai_router", {}) or {}
    out = {
        "keys": {p: "" for p in MODEL_CATALOG},  # API keys per provider
        "defaults": {                            # default model per persona
            "customer":  "anthropic/claude-opus-4-7",
            "admin":     "anthropic/claude-opus-4-7",
            "vendor":    "anthropic/claude-sonnet-4-6",
            "blog":      "anthropic/claude-opus-4-7",
            "video":     "anthropic/claude-opus-4-7",
        },
    }
    out["keys"].update(cur.get("keys") or {})
    out["defaults"].update(cur.get("defaults") or {})
    return out


def _save_cfg(d: dict) -> None:
    db.cfg_set("ai_router", d)


# ---------- API ----------
class KeysBody(BaseModel):
    keys: dict[str, str] | None = None
    defaults: dict[str, str] | None = None


@router.get("/catalog")
def catalog():
    cfg = _load_cfg()
    out = []
    for prov_id, info in MODEL_CATALOG.items():
        raw_key = (cfg["keys"].get(prov_id) or "").strip()
        out.append({
            "provider": prov_id,
            "label": info["label"],
            "key_env": info["key_env"],
            "key_set": bool(raw_key),
            "key_preview": (raw_key[:6] + "…" + raw_key[-4:]) if len(raw_key) >= 12 else "",
            "key_len": len(raw_key),
            # Full key only sent when admin clicks 'reveal' — gated by a separate endpoint
            "get_key_url": info.get("get_key_url"),
            "pricing_url": info.get("pricing_url"),
            "free_tier": info.get("free_tier"),
            "models": info["models"],
        })
    return {"providers": out, "defaults": cfg["defaults"]}


@router.get("/key/{provider}")
def reveal_key(provider: str):
    """Returns the FULL stored key for one provider — gated by admin auth (router-level).
    Frontend uses this only when the admin clicks 👁 'reveal' on a key."""
    if provider not in MODEL_CATALOG:
        raise HTTPException(404, "unknown provider")
    cfg = _load_cfg()
    return {"provider": provider, "key": (cfg["keys"].get(provider) or "")}


@router.post("/test/{provider}")
async def test_provider(provider: str):
    """Pings the provider with the cheapest model + a 1-word prompt to verify the key
    actually works. Returns {ok, latency_ms, model, sample, error?} so admin sees
    GREEN/RED status per provider."""
    if provider not in MODEL_CATALOG:
        raise HTTPException(404, "unknown provider")
    cfg = _load_cfg()
    key = (cfg["keys"].get(provider) or "").strip()
    if not key:
        return {"ok": False, "provider": provider, "error": "No key set — paste one above and Save first."}
    info = MODEL_CATALOG[provider]
    # Pick the cheapest/smallest model for the test (last in list is usually 'haiku/lite' tier)
    models = info.get("models") or []
    if not models:
        return {"ok": False, "provider": provider, "error": "No models defined for provider."}
    test_model = next((m["id"] for m in models if m.get("tier") in ("lite", "fast", "small")),
                      models[-1]["id"])
    # Use call_model with a tiny prompt so we exercise the real codepath
    res = await call_model(provider, test_model, "Reply with just the single word: ok", cfg)
    if res.get("ok"):
        sample = (res.get("text") or "").strip()[:60]
        return {"ok": True, "provider": provider, "model": test_model,
                "latency_ms": res.get("latency_ms"), "sample": sample,
                "msg": f"✅ Working — replied in {res.get('latency_ms')}ms with: \"{sample}\""}
    return {"ok": False, "provider": provider, "model": test_model,
            "latency_ms": res.get("latency_ms"),
            "error": res.get("error") or "unknown error"}


@router.post("/keys")
def save_keys(body: KeysBody):
    cur = _load_cfg()
    if body.keys:
        for k, v in body.keys.items():
            if k in MODEL_CATALOG:
                cur["keys"][k] = (v or "").strip()
    if body.defaults:
        for persona, model in body.defaults.items():
            if persona in cur["defaults"] and model:
                cur["defaults"][persona] = model
    _save_cfg(cur)
    return {"ok": True}


# ---------- providers ----------
async def _call_anthropic(key: str, model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": model, "max_tokens": 1024,
                  "messages": [{"role": "user", "content": prompt}]})
    if r.status_code >= 400: raise RuntimeError(f"anthropic {r.status_code}: {r.text[:200]}")
    j = r.json()
    return j.get("content", [{}])[0].get("text", "") or ""


async def _call_openai(key: str, model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}",
                     "content-type": "application/json"},
            json={"model": model, "max_tokens": 1024,
                  "messages": [{"role": "user", "content": prompt}]})
    if r.status_code >= 400: raise RuntimeError(f"openai {r.status_code}: {r.text[:200]}")
    j = r.json()
    return (j.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


async def _call_google(key: str, model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": prompt}]}]})
    if r.status_code >= 400: raise RuntimeError(f"google {r.status_code}: {r.text[:200]}")
    j = r.json()
    parts = (j.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


async def _call_openai_compatible(base: str, key: str, model: str, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
            json={"model": model, "max_tokens": 1024,
                  "messages": [{"role": "user", "content": prompt}]})
    if r.status_code >= 400: raise RuntimeError(f"{base} {r.status_code}: {r.text[:200]}")
    j = r.json()
    return (j.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


async def _call_anthropic_msgs(key: str, model: str, messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": model, "max_tokens": 1024, "messages": messages})
    if r.status_code >= 400: raise RuntimeError(f"anthropic {r.status_code}: {r.text[:200]}")
    j = r.json(); return j.get("content",[{}])[0].get("text","") or ""

async def _call_openai_compatible_msgs(base: str, key: str, model: str, messages: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
            json={"model": model, "max_tokens": 1024, "messages": messages})
    if r.status_code >= 400: raise RuntimeError(f"{base} {r.status_code}: {r.text[:200]}")
    j = r.json(); return (j.get("choices") or [{}])[0].get("message",{}).get("content","") or ""

async def _call_google_msgs(key: str, model: str, messages: list[dict]) -> str:
    contents = [{"role": "user" if m["role"]=="user" else "model",
                 "parts": [{"text": m["content"]}]} for m in messages]
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
            json={"contents": contents})
    if r.status_code >= 400: raise RuntimeError(f"google {r.status_code}: {r.text[:200]}")
    parts = (r.json().get("candidates") or [{}])[0].get("content",{}).get("parts",[])
    return "".join(p.get("text","") for p in parts)


async def call_model(provider: str, model: str, prompt: str, cfg: dict | None = None,
                     history: list[dict] | None = None) -> dict:
    """Returns {ok, provider, model, text, latency_ms, error?, ...}.
    If `history` is given, it's the prior conversation (prepended to the new
    user prompt) so chat-mode keeps context."""
    cfg = cfg or _load_cfg()
    key = (cfg["keys"].get(provider) or "").strip()
    if not key:
        return {"ok": False, "provider": provider, "model": model,
                "error": f"No API key set for {provider}. Add it in admin → AI."}
    messages = (history or []) + [{"role": "user", "content": prompt}]
    started = time.perf_counter()
    try:
        if provider == "anthropic":
            text = await _call_anthropic_msgs(key, model, messages)
        elif provider == "openai":
            text = await _call_openai_compatible_msgs("https://api.openai.com/v1", key, model, messages)
        elif provider == "google":
            text = await _call_google_msgs(key, model, messages)
        elif provider == "mistral":
            text = await _call_openai_compatible_msgs("https://api.mistral.ai/v1", key, model, messages)
        elif provider == "deepseek":
            text = await _call_openai_compatible_msgs("https://api.deepseek.com/v1", key, model, messages)
        elif provider == "groq":
            text = await _call_openai_compatible_msgs("https://api.groq.com/openai/v1", key, model, messages)
        elif provider == "together":
            text = await _call_openai_compatible_msgs("https://api.together.xyz/v1", key, model, messages)
        elif provider == "openrouter":
            text = await _call_openai_compatible_msgs("https://openrouter.ai/api/v1", key, model, messages)
        else:
            return {"ok": False, "provider": provider, "model": model, "error": "unknown provider"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "provider": provider, "model": model, "error": str(e),
                "latency_ms": int((time.perf_counter() - started) * 1000)}
    return {"ok": True, "provider": provider, "model": model, "text": text,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "char_count": len(text)}


class ArenaBody(BaseModel):
    prompt: str
    targets: list[str]
    history: list[dict] | None = None  # [{role, content}] — prior conversation for chat-mode


@router.post("/arena")
async def arena(body: ArenaBody):
    """Fan out the new prompt to multiple selected models with optional prior
    history for chat-mode continuity. Each target = 'provider/model_id'."""
    if not body.targets:
        raise HTTPException(400, "no targets selected")
    cfg = _load_cfg()
    tasks = []
    for t in body.targets:
        if "/" not in t: continue
        provider, model = t.split("/", 1)
        tasks.append(call_model(provider, model, body.prompt, cfg, history=body.history))
    if not tasks:
        raise HTTPException(400, "invalid targets")
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return {"ok": True, "results": results}
