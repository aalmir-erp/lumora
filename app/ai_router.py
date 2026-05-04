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
        "models": [
            {"id": "claude-opus-4-7",       "tier": "premium", "label": "Claude Opus 4.7"},
            {"id": "claude-sonnet-4-6",     "tier": "balanced","label": "Claude Sonnet 4.6"},
            {"id": "claude-haiku-4-5-20251001", "tier": "fast", "label": "Claude Haiku 4.5"},
        ],
    },
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "key_env": "OPENAI_API_KEY",
        "models": [
            {"id": "gpt-4o",      "tier": "premium",  "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "tier": "fast",     "label": "GPT-4o mini"},
            {"id": "o1-mini",     "tier": "premium",  "label": "o1-mini (reasoning)"},
        ],
    },
    "google": {
        "label": "Google (Gemini)",
        "key_env": "GOOGLE_API_KEY",
        "models": [
            {"id": "gemini-1.5-pro",   "tier": "premium", "label": "Gemini 1.5 Pro"},
            {"id": "gemini-1.5-flash", "tier": "fast",    "label": "Gemini 1.5 Flash (FREE tier)"},
        ],
    },
    "mistral": {
        "label": "Mistral",
        "key_env": "MISTRAL_API_KEY",
        "models": [
            {"id": "mistral-large-latest", "tier": "premium",  "label": "Mistral Large"},
            {"id": "mistral-small-latest", "tier": "balanced", "label": "Mistral Small"},
            {"id": "open-mistral-7b",      "tier": "free",     "label": "Open Mistral 7B (cheap)"},
        ],
    },
    "deepseek": {
        "label": "DeepSeek (cheap + capable)",
        "key_env": "DEEPSEEK_API_KEY",
        "models": [
            {"id": "deepseek-chat",     "tier": "balanced", "label": "DeepSeek Chat"},
            {"id": "deepseek-reasoner", "tier": "premium",  "label": "DeepSeek Reasoner"},
        ],
    },
    "groq": {
        "label": "Groq (fast inference, free tier)",
        "key_env": "GROQ_API_KEY",
        "models": [
            {"id": "llama-3.3-70b-versatile",  "tier": "free", "label": "Llama 3.3 70B (FREE)"},
            {"id": "mixtral-8x7b-32768",       "tier": "free", "label": "Mixtral 8x7B (FREE)"},
            {"id": "gemma2-9b-it",             "tier": "free", "label": "Gemma 2 9B (FREE)"},
        ],
    },
    "together": {
        "label": "Together AI (open models)",
        "key_env": "TOGETHER_API_KEY",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "tier": "free",     "label": "Llama 3.3 70B Turbo"},
            {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo",         "tier": "balanced", "label": "Qwen 2.5 72B"},
        ],
    },
    "openrouter": {
        "label": "OpenRouter (any model, one key)",
        "key_env": "OPENROUTER_API_KEY",
        "models": [
            {"id": "anthropic/claude-opus-4",     "tier": "premium", "label": "Claude Opus 4 (via OR)"},
            {"id": "openai/gpt-4o",               "tier": "premium", "label": "GPT-4o (via OR)"},
            {"id": "google/gemini-pro-1.5",       "tier": "premium", "label": "Gemini 1.5 Pro (via OR)"},
            {"id": "meta-llama/llama-3.3-70b-instruct:free", "tier": "free", "label": "Llama 3.3 70B (FREE)"},
            {"id": "deepseek/deepseek-chat",      "tier": "balanced","label": "DeepSeek Chat (via OR)"},
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
        out.append({
            "provider": prov_id,
            "label": info["label"],
            "key_env": info["key_env"],
            "key_set": bool(cfg["keys"].get(prov_id)),
            "models": info["models"],
        })
    return {"providers": out, "defaults": cfg["defaults"]}


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


async def call_model(provider: str, model: str, prompt: str, cfg: dict | None = None) -> dict:
    """Returns {ok, provider, model, text, latency_ms, error?}"""
    cfg = cfg or _load_cfg()
    key = (cfg["keys"].get(provider) or "").strip()
    if not key:
        return {"ok": False, "provider": provider, "model": model,
                "error": f"No API key set for {provider}. Add it in admin → AI."}
    started = time.perf_counter()
    try:
        if provider == "anthropic":
            text = await _call_anthropic(key, model, prompt)
        elif provider == "openai":
            text = await _call_openai(key, model, prompt)
        elif provider == "google":
            text = await _call_google(key, model, prompt)
        elif provider == "mistral":
            text = await _call_openai_compatible("https://api.mistral.ai/v1", key, model, prompt)
        elif provider == "deepseek":
            text = await _call_openai_compatible("https://api.deepseek.com/v1", key, model, prompt)
        elif provider == "groq":
            text = await _call_openai_compatible("https://api.groq.com/openai/v1", key, model, prompt)
        elif provider == "together":
            text = await _call_openai_compatible("https://api.together.xyz/v1", key, model, prompt)
        elif provider == "openrouter":
            text = await _call_openai_compatible("https://openrouter.ai/api/v1", key, model, prompt)
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
    targets: list[str]   # ["anthropic/claude-opus-4-7", "openai/gpt-4o", ...]


@router.post("/arena")
async def arena(body: ArenaBody):
    """Fan out prompt to multiple selected models in parallel; return responses
    side-by-side. Each target = 'provider/model_id'."""
    if not body.targets:
        raise HTTPException(400, "no targets selected")
    cfg = _load_cfg()
    tasks = []
    for t in body.targets:
        if "/" not in t: continue
        provider, model = t.split("/", 1)
        tasks.append(call_model(provider, model, body.prompt, cfg))
    if not tasks:
        raise HTTPException(400, "invalid targets")
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return {"ok": True, "results": results}
