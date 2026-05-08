# Aalmir Plastic — WhatsApp AI Chatbot

A senior-grade WhatsApp chatbot for **aalmirplastic.com**, built on the
official Meta WhatsApp Cloud API with a provider-agnostic AI layer
(Anthropic Claude or OpenAI GPT, switchable via env var).

## Features

- Meta WhatsApp Cloud API webhook (signature-verified, no third-party gateway)
- Provider-agnostic AI core — drop in Claude or OpenAI without touching business logic
- Anthropic prompt caching for the system prompt + product KB (cost control on repeat traffic)
- Per-user conversation memory (in-process dict, Redis-pluggable)
- Hardened "senior chatbot" persona: anti-hallucination, escalation rules, multilingual (EN / AR / UR / HI)
- FastAPI service, Docker-ready, single-file Procfile for Railway/Render

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in keys
uvicorn app.main:app --reload --port 8000
```

Expose locally with ngrok and point Meta's webhook to
`https://<your-tunnel>/webhook`.

## Wiring to Meta WhatsApp Cloud API

1. Create a Meta App at <https://developers.facebook.com/apps/>, add the
   "WhatsApp" product.
2. Get a **Permanent Access Token** (System User token recommended for
   production; the temporary 24h dev token works for testing).
3. Note the **Phone Number ID** and **WhatsApp Business Account ID**.
4. Set webhook to `https://<your-host>/webhook`, verify token = whatever
   you put in `META_VERIFY_TOKEN`.
5. Subscribe to the `messages` field on the WhatsApp Business Account.
6. Add your test recipient under "API Setup" until the number is fully
   verified for production.

See `.env.example` for the full env-var list.

## Switching AI providers

```
AI_PROVIDER=anthropic   # default — uses claude-sonnet-4-6
AI_PROVIDER=openai      # uses gpt-4.1 (configurable)
```

Both providers share the same `AIProvider` interface in `app/ai/base.py`,
so the rest of the app is provider-agnostic.

## Project layout

```
whatsapp_ai_chatbot/
├── app/
│   ├── main.py              FastAPI + webhook
│   ├── config.py            pydantic-settings
│   ├── whatsapp.py          Meta Cloud API client + HMAC verification
│   ├── persona.py           System prompt for Aalmir Plastic
│   ├── kb.py                Product / company knowledge base
│   ├── conversation.py      Per-user history store
│   └── ai/
│       ├── base.py          AIProvider protocol
│       ├── anthropic_provider.py
│       ├── openai_provider.py
│       └── factory.py
├── tests/
├── Dockerfile
├── Procfile
├── requirements.txt
└── .env.example
```

## Deployment

- **Railway / Render**: push the repo, set env vars, the included `Procfile`
  starts uvicorn on `$PORT`.
- **Docker**: `docker build -t aalmir-wa-bot . && docker run -p 8000:8000 --env-file .env aalmir-wa-bot`

## Customising the bot

- Update product / pricing / lead-time facts in `app/kb.py`.
- Tone, escalation rules, and language policy live in `app/persona.py`.
- Both files are deliberately kept small and human-editable — non-engineers
  on the Aalmir team can tune them.

## Security notes

- **Always verify Meta's HMAC signature** (handled in `app/whatsapp.py`).
  Reject any unsigned or mismatched webhook.
- Treat `META_APP_SECRET` and `META_ACCESS_TOKEN` like passwords — set them
  as service env vars, never commit them.
- Rate-limit the webhook at the edge (Cloudflare / Railway / nginx). Meta
  retries aggressively on 5xx, so return 200 quickly even when the AI call
  fails — log + escalate, never block the webhook.
