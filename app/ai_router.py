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
        "modality": "text",
        "models": [
            {"id": "claude-opus-4-7",            "tier": "premium",  "modality": "text", "label": "Claude Opus 4.7 (smartest)",     "price_per_1m": "$15 in / $75 out"},
            {"id": "claude-sonnet-4-6",          "tier": "balanced", "modality": "text", "label": "Claude Sonnet 4.6 (best value)", "price_per_1m": "$3 in / $15 out"},
            {"id": "claude-haiku-4-5-20251001",  "tier": "fast",     "modality": "text", "label": "Claude Haiku 4.5 (cheapest)",    "price_per_1m": "$0.80 in / $4 out"},
            {"id": "claude-3-5-sonnet-20241022", "tier": "balanced", "modality": "text", "label": "Claude 3.5 Sonnet (legacy)",     "price_per_1m": "$3 in / $15 out"},
            {"id": "claude-3-5-haiku-20241022",  "tier": "fast",     "modality": "text", "label": "Claude 3.5 Haiku (legacy)",      "price_per_1m": "$0.80 in / $4 out"},
            {"id": "claude-3-opus-20240229",     "tier": "premium",  "modality": "text", "label": "Claude 3 Opus (legacy)",         "price_per_1m": "$15 in / $75 out"},
        ],
    },
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "key_env": "OPENAI_API_KEY",
        "get_key_url": "https://platform.openai.com/api-keys",
        "pricing_url": "https://openai.com/api/pricing/",
        "free_tier": "No free tier — pay as you go",
        "modality": "text",
        "models": [
            {"id": "gpt-4o",          "tier": "premium",  "modality": "text", "label": "GPT-4o",                      "price_per_1m": "$2.50 in / $10 out"},
            {"id": "gpt-4o-mini",     "tier": "fast",     "modality": "text", "label": "GPT-4o mini (cheapest)",      "price_per_1m": "$0.15 in / $0.60 out"},
            {"id": "gpt-4-turbo",     "tier": "premium",  "modality": "text", "label": "GPT-4 Turbo",                 "price_per_1m": "$10 in / $30 out"},
            {"id": "gpt-4",           "tier": "premium",  "modality": "text", "label": "GPT-4 (classic)",             "price_per_1m": "$30 in / $60 out"},
            {"id": "gpt-3.5-turbo",   "tier": "fast",     "modality": "text", "label": "GPT-3.5 Turbo",               "price_per_1m": "$0.50 in / $1.50 out"},
            {"id": "o1",              "tier": "premium",  "modality": "text", "label": "o1 (reasoning, slow)",        "price_per_1m": "$15 in / $60 out"},
            {"id": "o1-mini",         "tier": "premium",  "modality": "text", "label": "o1-mini (reasoning, faster)", "price_per_1m": "$3 in / $12 out"},
            {"id": "o3-mini",         "tier": "premium",  "modality": "text", "label": "o3-mini (reasoning, newest)", "price_per_1m": "$1.10 in / $4.40 out"},
        ],
    },
    "google": {
        "label": "Google (Gemini)",
        "key_env": "GOOGLE_API_KEY",
        "get_key_url": "https://aistudio.google.com/app/apikey",
        "pricing_url": "https://ai.google.dev/pricing",
        "free_tier": "FREE up to 15 req/min · 1.5K req/day for Flash",
        "modality": "text",
        "models": [
            {"id": "gemini-2.5-pro",            "tier": "premium",  "modality": "text", "label": "Gemini 2.5 Pro (latest, smartest)", "price_per_1m": "$1.25 in / $10 out"},
            {"id": "gemini-2.5-flash",          "tier": "free",     "modality": "text", "label": "Gemini 2.5 Flash (FREE tier)",      "price_per_1m": "FREE / $0.30 in"},
            {"id": "gemini-2.5-flash-lite",     "tier": "fast",     "modality": "text", "label": "Gemini 2.5 Flash Lite",             "price_per_1m": "$0.10 in / $0.40 out"},
            {"id": "gemini-1.5-pro",            "tier": "premium",  "modality": "text", "label": "Gemini 1.5 Pro",                    "price_per_1m": "$1.25 in / $5 out"},
            {"id": "gemini-1.5-flash",          "tier": "fast",     "modality": "text", "label": "Gemini 1.5 Flash (FREE)",           "price_per_1m": "FREE up to 1.5K req/day"},
            {"id": "gemini-1.5-flash-8b",       "tier": "fast",     "modality": "text", "label": "Gemini 1.5 Flash-8B (cheapest)",    "price_per_1m": "$0.04 in / $0.15 out"},
        ],
    },
    "google_image": {
        "label": "Google Imagen / Nano Banana 🍌 (image gen)",
        "key_env": "GOOGLE_API_KEY",     # same key as text Gemini
        "get_key_url": "https://aistudio.google.com/app/apikey",
        "pricing_url": "https://ai.google.dev/pricing",
        "free_tier": "FREE tier in AI Studio",
        "modality": "image",
        "models": [
            {"id": "gemini-2.5-flash-image",     "tier": "premium",  "modality": "image", "label": "Nano Banana 🍌 (Gemini 2.5 Flash Image)", "price_per_1m": "$30 / 1M output tokens (~$0.039 per image)"},
            {"id": "imagen-3.0-generate-002",    "tier": "premium",  "modality": "image", "label": "Imagen 3 (highest quality)", "price_per_1m": "$0.04 per image"},
            {"id": "imagen-3.0-fast-generate-001","tier": "fast",    "modality": "image", "label": "Imagen 3 Fast",              "price_per_1m": "$0.02 per image"},
        ],
    },
    "openai_image": {
        "label": "OpenAI image generation (DALL-E)",
        "key_env": "OPENAI_API_KEY",
        "get_key_url": "https://platform.openai.com/api-keys",
        "pricing_url": "https://openai.com/api/pricing/",
        "free_tier": "No free tier",
        "modality": "image",
        "models": [
            {"id": "dall-e-3",       "tier": "premium",  "modality": "image", "label": "DALL-E 3",          "price_per_1m": "$0.04 per image (1024x1024)"},
            {"id": "dall-e-2",       "tier": "fast",     "modality": "image", "label": "DALL-E 2 (cheaper)","price_per_1m": "$0.02 per image"},
            {"id": "gpt-image-1",    "tier": "premium",  "modality": "image", "label": "GPT-Image-1 (newest)","price_per_1m": "$0.04 per image"},
        ],
    },
    "stability": {
        "label": "Stability AI (Stable Diffusion)",
        "key_env": "STABILITY_API_KEY",
        "get_key_url": "https://platform.stability.ai/account/keys",
        "pricing_url": "https://platform.stability.ai/pricing",
        "free_tier": "25 free credits on signup",
        "modality": "image",
        "models": [
            {"id": "sd3.5-large",       "tier": "premium",  "modality": "image", "label": "Stable Diffusion 3.5 Large", "price_per_1m": "$0.065 per image"},
            {"id": "sd3.5-medium",      "tier": "balanced", "modality": "image", "label": "SD 3.5 Medium",              "price_per_1m": "$0.035 per image"},
            {"id": "sd3-large-turbo",   "tier": "fast",     "modality": "image", "label": "SD 3 Large Turbo",           "price_per_1m": "$0.04 per image"},
            {"id": "core",              "tier": "fast",     "modality": "image", "label": "Stable Image Core",          "price_per_1m": "$0.03 per image"},
        ],
    },
    "xai": {
        "label": "xAI (Grok by X)",
        "key_env": "XAI_API_KEY",
        "get_key_url": "https://console.x.ai/",
        "pricing_url": "https://docs.x.ai/docs/models",
        "free_tier": "$25 free monthly credit (with billing setup)",
        "modality": "text",
        "models": [
            {"id": "grok-4",            "tier": "premium",  "modality": "text", "label": "Grok 4 (latest, smartest)",   "price_per_1m": "$5 in / $15 out"},
            {"id": "grok-3",            "tier": "premium",  "modality": "text", "label": "Grok 3",                       "price_per_1m": "$3 in / $15 out"},
            {"id": "grok-3-mini",       "tier": "fast",     "modality": "text", "label": "Grok 3 mini (cheapest)",       "price_per_1m": "$0.30 in / $0.50 out"},
            {"id": "grok-2-vision-1212","tier": "balanced", "modality": "text", "label": "Grok 2 Vision",                "price_per_1m": "$2 in / $10 out"},
            {"id": "grok-beta",         "tier": "balanced", "modality": "text", "label": "Grok beta",                    "price_per_1m": "$5 in / $15 out"},
        ],
    },
    "mistral": {
        "label": "Mistral",
        "key_env": "MISTRAL_API_KEY",
        "get_key_url": "https://console.mistral.ai/api-keys",
        "pricing_url": "https://mistral.ai/products/la-plateforme#pricing",
        "free_tier": "Free dev tier (rate-limited)",
        "modality": "text",
        "models": [
            {"id": "mistral-large-latest",     "tier": "premium",  "modality": "text", "label": "Mistral Large 2",         "price_per_1m": "$2 in / $6 out"},
            {"id": "mistral-medium-latest",    "tier": "balanced", "modality": "text", "label": "Mistral Medium",          "price_per_1m": "$2.70 in / $8.10 out"},
            {"id": "mistral-small-latest",     "tier": "fast",     "modality": "text", "label": "Mistral Small (cheap)",   "price_per_1m": "$0.20 in / $0.60 out"},
            {"id": "codestral-latest",         "tier": "balanced", "modality": "text", "label": "Codestral (code-tuned)",  "price_per_1m": "$0.30 in / $0.90 out"},
            {"id": "pixtral-large-latest",     "tier": "premium",  "modality": "text", "label": "Pixtral Large (vision)",  "price_per_1m": "$2 in / $6 out"},
            {"id": "open-mistral-7b",          "tier": "fast",     "modality": "text", "label": "Open Mistral 7B",         "price_per_1m": "$0.25 in / $0.25 out"},
        ],
    },
    "deepseek": {
        "label": "DeepSeek (cheap + capable)",
        "key_env": "DEEPSEEK_API_KEY",
        "get_key_url": "https://platform.deepseek.com/api_keys",
        "pricing_url": "https://api-docs.deepseek.com/quick_start/pricing",
        "free_tier": "$5 free credit on signup",
        "modality": "text",
        "models": [
            {"id": "deepseek-chat",     "tier": "balanced", "modality": "text", "label": "DeepSeek V3 Chat",            "price_per_1m": "$0.27 in / $1.10 out"},
            {"id": "deepseek-reasoner", "tier": "premium",  "modality": "text", "label": "DeepSeek R1 Reasoner",        "price_per_1m": "$0.55 in / $2.19 out"},
            {"id": "deepseek-coder",    "tier": "balanced", "modality": "text", "label": "DeepSeek Coder",              "price_per_1m": "$0.27 in / $1.10 out"},
        ],
    },
    "groq": {
        "label": "Groq (LPU, fastest inference, free tier)",
        "key_env": "GROQ_API_KEY",
        "get_key_url": "https://console.groq.com/keys",
        "pricing_url": "https://console.groq.com/pricing",
        "free_tier": "FREE tier — 30 req/min, no card required",
        "modality": "text",
        "models": [
            {"id": "llama-3.3-70b-versatile",       "tier": "free",    "modality": "text", "label": "Llama 3.3 70B (FREE)",       "price_per_1m": "$0.59 in / $0.79 out"},
            {"id": "llama-3.1-8b-instant",          "tier": "free",    "modality": "text", "label": "Llama 3.1 8B Instant (FREE)","price_per_1m": "$0.05 in / $0.08 out"},
            {"id": "llama-3.2-90b-vision-preview",  "tier": "premium", "modality": "text", "label": "Llama 3.2 90B Vision",       "price_per_1m": "$0.90 in / $0.90 out"},
            {"id": "gemma2-9b-it",                  "tier": "free",    "modality": "text", "label": "Gemma 2 9B (FREE)",          "price_per_1m": "$0.20 in / $0.20 out"},
            {"id": "deepseek-r1-distill-llama-70b", "tier": "free",    "modality": "text", "label": "DeepSeek R1 Distill 70B",    "price_per_1m": "$0.75 in / $0.99 out"},
        ],
    },
    "together": {
        "label": "Together AI (open models)",
        "key_env": "TOGETHER_API_KEY",
        "get_key_url": "https://api.together.xyz/settings/api-keys",
        "pricing_url": "https://www.together.ai/pricing",
        "free_tier": "$1 free credit on signup",
        "modality": "text",
        "models": [
            {"id": "meta-llama/Llama-3.3-70B-Instruct-Turbo",     "tier": "balanced", "modality": "text", "label": "Llama 3.3 70B Turbo",   "price_per_1m": "$0.88"},
            {"id": "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo","tier": "premium", "modality": "text", "label": "Llama 3.1 405B Turbo",  "price_per_1m": "$3.50"},
            {"id": "Qwen/Qwen2.5-72B-Instruct-Turbo",             "tier": "balanced", "modality": "text", "label": "Qwen 2.5 72B Turbo",    "price_per_1m": "$1.20"},
            {"id": "Qwen/Qwen2.5-Coder-32B-Instruct",             "tier": "balanced", "modality": "text", "label": "Qwen 2.5 Coder 32B",    "price_per_1m": "$0.80"},
            {"id": "deepseek-ai/DeepSeek-V3",                     "tier": "balanced", "modality": "text", "label": "DeepSeek V3 (Together)","price_per_1m": "$1.25"},
            {"id": "mistralai/Mixtral-8x22B-Instruct-v0.1",       "tier": "premium",  "modality": "text", "label": "Mixtral 8x22B",         "price_per_1m": "$1.20"},
        ],
    },
    "openrouter": {
        "label": "OpenRouter (any model, one key)",
        "key_env": "OPENROUTER_API_KEY",
        "get_key_url": "https://openrouter.ai/keys",
        "pricing_url": "https://openrouter.ai/models",
        "free_tier": "FREE tier on selected models (rate-limited)",
        "modality": "text",
        "models": [
            {"id": "meta-llama/llama-3.3-70b-instruct:free",       "tier": "free",     "modality": "text", "label": "Llama 3.3 70B (FREE)",     "price_per_1m": "FREE"},
            {"id": "google/gemini-2.0-flash-exp:free",             "tier": "free",     "modality": "text", "label": "Gemini 2.0 Flash (FREE)",  "price_per_1m": "FREE"},
            {"id": "anthropic/claude-opus-4",                      "tier": "premium",  "modality": "text", "label": "Claude Opus 4 (via OR)",   "price_per_1m": "$15 in / $75 out"},
            {"id": "anthropic/claude-sonnet-4",                    "tier": "balanced", "modality": "text", "label": "Claude Sonnet 4 (via OR)", "price_per_1m": "$3 in / $15 out"},
            {"id": "openai/gpt-4o",                                "tier": "premium",  "modality": "text", "label": "GPT-4o (via OR)",          "price_per_1m": "$2.50 in / $10 out"},
            {"id": "openai/o1",                                    "tier": "premium",  "modality": "text", "label": "o1 (via OR)",              "price_per_1m": "$15 in / $60 out"},
            {"id": "google/gemini-2.5-pro",                        "tier": "premium",  "modality": "text", "label": "Gemini 2.5 Pro (via OR)",  "price_per_1m": "$1.25 in / $10 out"},
            {"id": "x-ai/grok-4",                                  "tier": "premium",  "modality": "text", "label": "Grok 4 (via OR)",          "price_per_1m": "$5 in / $15 out"},
            {"id": "deepseek/deepseek-chat",                       "tier": "balanced", "modality": "text", "label": "DeepSeek Chat (via OR)",   "price_per_1m": "$0.27 in / $1.10 out"},
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
            # Long-form content prefers OpenAI/Google by default — cheaper for
            # cron + survives Anthropic credit dips. Cascade still tries
            # Anthropic later in the chain.
            "blog":      "openai/gpt-4o",
            "video":     "google/gemini-2.5-pro",
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
    """Pings the provider with the cheapest model to verify the key works.
    For text providers: 1-word prompt. For image providers: cheap image gen
    with prompt 'a tiny servia mascot'. Returns ok/latency/sample for green/red."""
    if provider not in MODEL_CATALOG:
        raise HTTPException(404, "unknown provider")
    cfg = _load_cfg()
    key = (cfg["keys"].get(provider) or "").strip()
    if not key:
        return {"ok": False, "provider": provider, "error": "No key set — paste one above and Save first."}
    info = MODEL_CATALOG[provider]
    models = info.get("models") or []
    if not models:
        return {"ok": False, "provider": provider, "error": "No models defined for provider."}
    test_model = next(
        (m["id"] for m in models if m.get("tier") in ("free", "lite", "fast", "small")),
        next((m["id"] for m in models if m.get("tier") == "balanced"), models[0]["id"]))
    is_image = (info.get("modality") == "image")
    if is_image:
        res = await call_image_model(provider, test_model,
                                     "A tiny smiling servia mascot, simple vector style", cfg)
        if res.get("ok"):
            return {"ok": True, "provider": provider, "model": test_model,
                    "latency_ms": res.get("latency_ms"),
                    "image_url": res.get("image_url"),
                    "image_data_url": res.get("image_data_url"),
                    "sample": "(image generated)",
                    "msg": f"✅ Working — generated image in {res.get('latency_ms')}ms"}
        return {"ok": False, "provider": provider, "model": test_model,
                "latency_ms": res.get("latency_ms"),
                "error": res.get("error") or "unknown error"}
    # text providers
    res = await call_model(provider, test_model, "Reply with just the single word: ok", cfg)
    if res.get("ok"):
        sample = (res.get("text") or "").strip()[:60]
        return {"ok": True, "provider": provider, "model": test_model,
                "latency_ms": res.get("latency_ms"), "sample": sample,
                "msg": f"✅ Working — replied in {res.get('latency_ms')}ms with: \"{sample}\""}
    err = (res.get("error") or "").lower()
    # Special-case "key works but billing depleted" — this is NOT a key issue
    if any(s in err for s in ("insufficient balance", "insufficient_quota",
                              "balance is too low", "exceeded your current quota",
                              "billing", "402")):
        return {"ok": False, "provider": provider, "model": test_model,
                "latency_ms": res.get("latency_ms"),
                "key_valid": True,    # tells the UI to show yellow not red
                "error": res.get("error") or "unknown error",
                "msg": "🟡 Key valid — but provider account has $0 balance. Top up to use this provider."}
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


async def call_with_cascade(prompt: str, *, persona: str = "blog",
                            preferred: str | None = None,
                            cfg: dict | None = None) -> dict:
    """Try the admin's preferred model first, then cascade through providers
    that have keys configured. Returns the first successful result, or the
    last error if every provider fails. Saves admin from manual fallbacks
    when one provider runs out of credit / rate-limits."""
    cfg = cfg or _load_cfg()
    keys = cfg.get("keys") or {}
    defaults = cfg.get("defaults") or {}

    # 1. Build provider order: preferred → persona-default → fallback chain
    chain: list[str] = []
    def _push(m: str | None):
        if not m or "/" not in m: return
        if m not in chain: chain.append(m)
    _push(preferred)
    _push(defaults.get(persona))
    # Cheap/reliable fallbacks for prose tasks
    for m in ("openai/gpt-4o", "google/gemini-2.5-pro",
              "anthropic/claude-opus-4-7", "openai/gpt-4o-mini",
              "google/gemini-2.0-flash-exp",
              "openrouter/google/gemini-2.0-flash-exp:free",
              "openrouter/meta-llama/llama-3.3-70b-instruct:free",
              "groq/llama-3.3-70b-versatile",
              "deepseek/deepseek-chat", "xai/grok-2-1212",
              "mistral/mistral-large-latest"):
        _push(m)

    last_err = None
    tried: list[dict] = []
    for entry in chain:
        provider, _, model = entry.partition("/")
        # OpenRouter-style entries (provider/model/sub) — keep model intact
        if provider == "openrouter" and "/" not in model:
            # already model-only
            pass
        if not (keys.get(provider) or "").strip():
            tried.append({"provider": provider, "model": model, "ok": False, "error": "no key"})
            continue
        res = await call_model(provider, model, prompt, cfg)
        tried.append({"provider": provider, "model": model, "ok": res.get("ok"),
                      "error": res.get("error") or ""})
        if res.get("ok"):
            res["tried"] = tried
            return res
        # Anthropic credit/billing error → drop down to next provider quietly
        last_err = res
    return {"ok": False, "error": "All providers failed",
            "tried": tried, "last_error": (last_err or {}).get("error", "")}


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
        elif provider == "xai":
            text = await _call_openai_compatible_msgs("https://api.x.ai/v1", key, model, messages)
        else:
            return {"ok": False, "provider": provider, "model": model, "error": "unknown provider (or image-modality — use call_image_model instead)"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "provider": provider, "model": model, "error": str(e),
                "latency_ms": int((time.perf_counter() - started) * 1000)}
    return {"ok": True, "provider": provider, "model": model, "text": text,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "char_count": len(text)}


# ---------- image generation ----------
async def _call_google_image(key: str, model: str, prompt: str, *, n: int = 1, size: str = "1024x1024") -> dict:
    """Calls Gemini's image generation (Nano Banana / Imagen 3 family). Returns
    {image_data_url} — base64 PNG inline so admin can preview without storage."""
    # Imagen-3 uses the predict endpoint; nano banana (gemini-2.5-flash-image) uses generateContent.
    if model.startswith("imagen-"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={key}"
        body = {"instances": [{"prompt": prompt}],
                "parameters": {"sampleCount": n, "aspectRatio": "1:1"}}
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(url, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"google_image {r.status_code}: {r.text[:200]}")
        j = r.json()
        preds = j.get("predictions", [])
        if not preds: raise RuntimeError(f"no image returned: {j}")
        b64 = preds[0].get("bytesBase64Encoded") or ""
        return {"image_data_url": f"data:image/png;base64,{b64}"}
    # Gemini 2.5 Flash Image (Nano Banana) via generateContent
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]}}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, json=body)
    if r.status_code >= 400:
        raise RuntimeError(f"google_image {r.status_code}: {r.text[:200]}")
    j = r.json()
    parts = (j.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    for p in parts:
        if "inlineData" in p:
            d = p["inlineData"]
            return {"image_data_url": f"data:{d.get('mimeType','image/png')};base64,{d.get('data','')}"}
    raise RuntimeError(f"no image part in response: {j}")


async def _call_openai_image(key: str, model: str, prompt: str, *, n: int = 1, size: str = "1024x1024") -> dict:
    """Calls DALL-E / gpt-image-1. Returns {image_url} (URL) or {image_data_url}."""
    payload = {"model": model, "prompt": prompt, "n": n, "size": size}
    if model == "gpt-image-1":
        payload["response_format"] = "b64_json"
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post("https://api.openai.com/v1/images/generations",
                         headers={"Authorization": f"Bearer {key}", "content-type": "application/json"},
                         json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"openai_image {r.status_code}: {r.text[:200]}")
    data = (r.json().get("data") or [{}])[0]
    if data.get("b64_json"):
        return {"image_data_url": f"data:image/png;base64,{data['b64_json']}"}
    return {"image_url": data.get("url", "")}


async def _call_stability_image(key: str, model: str, prompt: str) -> dict:
    """Stable Diffusion 3.5 / Core via Stability AI API."""
    # stable-image generate endpoint differs by model family
    base = "https://api.stability.ai/v2beta/stable-image/generate"
    # sd3.5-* → /sd3, core → /core, ultra → /ultra
    if "sd3" in model:    path = f"{base}/sd3"
    elif "core" in model: path = f"{base}/core"
    elif "ultra" in model:path = f"{base}/ultra"
    else: path = f"{base}/sd3"
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(path,
                         headers={"Authorization": f"Bearer {key}",
                                  "accept": "image/*"},
                         data={"prompt": prompt, "model": model, "output_format": "png"},
                         files={"none": ("none", b"")})  # multipart form required
    if r.status_code >= 400:
        raise RuntimeError(f"stability {r.status_code}: {r.text[:200]}")
    import base64 as _b64
    b64 = _b64.b64encode(r.content).decode()
    return {"image_data_url": f"data:image/png;base64,{b64}"}


async def call_image_model(provider: str, model: str, prompt: str,
                           cfg: dict | None = None) -> dict:
    """Returns {ok, image_data_url|image_url, latency_ms, ...}. Drop-in for
    any image-modality provider in MODEL_CATALOG."""
    cfg = cfg or _load_cfg()
    key = (cfg["keys"].get(provider) or "").strip()
    if not key:
        return {"ok": False, "provider": provider, "model": model,
                "error": f"No API key set for {provider}. Add it in admin → AI."}
    started = time.perf_counter()
    try:
        if provider == "google_image":
            res = await _call_google_image(key, model, prompt)
        elif provider == "openai_image":
            res = await _call_openai_image(key, model, prompt)
        elif provider == "stability":
            res = await _call_stability_image(key, model, prompt)
        else:
            return {"ok": False, "provider": provider, "model": model,
                    "error": "unknown image provider"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "provider": provider, "model": model, "error": str(e),
                "latency_ms": int((time.perf_counter() - started) * 1000)}
    return {"ok": True, "provider": provider, "model": model,
            "latency_ms": int((time.perf_counter() - started) * 1000),
            **res}


class ImageBody(BaseModel):
    provider: str = "google_image"
    model: str = "gemini-2.5-flash-image"
    prompt: str


@router.post("/image")
async def gen_image(body: ImageBody):
    """One-off image generation — admin clicks 'Generate' with a prompt,
    we return a base64 image inline. Provider must be modality=image."""
    if body.provider not in MODEL_CATALOG:
        raise HTTPException(400, f"unknown provider {body.provider}")
    info = MODEL_CATALOG[body.provider]
    if info.get("modality") != "image":
        raise HTTPException(400, f"provider {body.provider} is not an image generator")
    return await call_image_model(body.provider, body.model, body.prompt)


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
