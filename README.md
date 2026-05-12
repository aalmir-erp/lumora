# Servia — UAE smart home services platform

Modern, installable PWA + admin panel + AI concierge bot, all in one self-contained app.
Deploys on Railway from this folder. Brand name and colors configurable.

> **About the name.** *Lumora* = "lumo" (Latin / Esperanto for *light*) + "-ora"
> (a bright suffix from words like *aurora*) — evokes clean, luminous, premium.
> Easy to pronounce in EN / AR / HI / TL. Override with `BRAND_NAME=...`.

```
┌────────────────────────────────────────────────────────────────────┐
│  PWA website  ←→  FastAPI  ←→  Claude Opus 4.7 (tool use, caching) │
│       ↑              │                                              │
│  Service worker      │ tools: quote, slots, book, invoice, sign,   │
│  + manifest          │        whatsapp, handoff                    │
│       ↑              ↓                                              │
│  Admin panel    SQLite (volume)                                    │
│  Customer       │                                                  │
│  portal         WhatsApp Bridge (Node, separate Railway service)   │
└────────────────────────────────────────────────────────────────────┘
```

## What's in v0.2

**Frontend (PWA, installable, offline shell)**
- `index.html`     — landing (hero, services, features, testimonials)
- `services.html`  — full catalogue with category filter + search
- `book.html`      — instant quote + booking form (uses the bot's tools)
- `account.html`   — customer portal: track by phone or booking ID
- `quote.html`     — view quote, sign on screen, auto-creates invoice
- `admin.html`     — full admin (login + dashboard + bookings + convos + pricing + WA)
- `widget.js/css`  — embeddable bot bubble (drop on any site)
- `manifest.webmanifest`, `sw.js` — installable PWA, offline cache
- `app.js`         — i18n loader (EN / AR with RTL / HI / TL), API helper, install prompt

**Backend (FastAPI)**
- `app/main.py`     — wires everything; exposes `/api/*`, serves static
- `app/llm.py`      — Claude Opus 4.7 + adaptive thinking + prompt caching on KB
- `app/tools.py`    — 9 tools the bot can call
- `app/db.py`       — SQLite (single file on volume); bookings/quotes/invoices/conversations/events/config
- `app/quotes.py`   — quote → sign → invoice → payment-link flow (Stripe ready)
- `app/admin.py`    — admin CRUD + live agent takeover + SSE event stream
- `app/portal.py`   — customer-facing track + sign endpoints
- `app/whatsapp.py` — webhook from the QR bridge + push back via bridge
- `app/auth.py`     — single-token admin auth
- `app/demo_brain.py` — rule-based fallback when no `ANTHROPIC_API_KEY`

**WhatsApp QR bridge (separate Node service)**
- `whatsapp_bridge/index.js` — `whatsapp-web.js` + Express; QR page + `/send`
- Pairs your **personal WhatsApp** via QR scan (standard whatsapp-web.js flow)
- Forwards inbound msgs to FastAPI; FastAPI pushes replies back via `/send`
- Persistent session via `LocalAuth` directory (mount as Railway volume)

**Tests** — 11 passing (`pytest tests/`).

## Brand identity

| Asset      | Path           |
| ---------- | -------------- |
| Wordmark   | `/logo.svg`    |
| Avatar (mascot "Lumi") | `/avatar.svg`  |
| App icons  | `/icon-192.svg`, `/icon-512.svg` |
| Colors     | primary `#0D9488` · primary-dark `#115E59` · accent `#F59E0B` |
| Typography | system-ui (Inter / Segoe UI / Roboto fallback) |

Edit the brand at runtime via env vars: `BRAND_NAME`, `BRAND_TAGLINE`, `BRAND_DOMAIN`,
or override colors in `web/style.css`.

## Services + competitive pricing

17 services at competitive UAE-market rates — fully editable from the admin
panel (`/admin.html → Pricing`). Overrides land in `config.pricing_overrides`
and merge over the file-based defaults; no redeploy needed.

| Service | Starting price (AED) |
| --- | --- |
| General Cleaning | 200 (1BR) |
| Deep Cleaning | 350 (1BR) |
| Move-in / Move-out | 600 (1BR) |
| Hourly Maid | 35/hr |
| Office Cleaning | 120/3h |
| Post-Construction | 240/4h |
| Sofa & Carpet | 35/seat, 12/sqm |
| AC Cleaning | 150/split unit |
| Disinfection | 250 |
| Window Cleaning | 150 |
| Pest Control | 220 |
| Laundry & Ironing | 7/piece |
| Babysitting | 40/hr |
| Gardening | 180 |
| Handyman | 120/hr |
| Kitchen Deep | 300 |
| Villa Deep | 1,100 |

## Quickstart (local)

```bash
cd urbanservices_chatbot
pip install -r requirements.txt
DEMO_MODE=on uvicorn app.main:app --reload
```

Open http://localhost:8000.

For the admin panel:
```bash
ADMIN_TOKEN=mySecret DEMO_MODE=on uvicorn app.main:app --reload
# then open /admin.html and paste mySecret
```

When you set `ANTHROPIC_API_KEY`, the bot switches to Claude Opus 4.7.

## Deploy on Railway (sales.mir.ae)

This is a **monorepo** — only redeploys when files under `urbanservices_chatbot/**`
change (configured via `watchPaths` in `railway.json`).

1. **Service A — Bot + Website**
   - Build: `urbanservices_chatbot/Dockerfile`
   - Volume: mount at `/data` (SQLite lives here)
   - Env vars:
     ```
     ANTHROPIC_API_KEY=sk-ant-...
     ADMIN_TOKEN=<long random>
     BRAND_NAME=Lumora
     BRAND_DOMAIN=sales.mir.ae
     ALLOWED_ORIGINS=https://sales.mir.ae,https://www.sales.mir.ae
     STRIPE_SECRET_KEY=sk_live_...           # optional, for live payments
     WA_BRIDGE_URL=https://<bridge>.railway.app
     WA_BRIDGE_TOKEN=<shared-secret>
     ```
   - Custom domain → `sales.mir.ae`

2. **Service B — WhatsApp QR bridge**
   - Build: `urbanservices_chatbot/whatsapp_bridge/Dockerfile`
   - Volume: mount at `/app/.wwebjs_auth` (so QR session survives redeploys)
   - Env: `BOT_WEBHOOK=https://sales.mir.ae/api/wa/webhook`, `BRIDGE_TOKEN=<same secret>`
   - After deploy, open `/qr` (with `Authorization: Bearer <token>`) and scan with phone

## Endpoints

| Path | Method | Auth | Use |
| --- | --- | --- | --- |
| `/api/health` | GET | none | health + mode + WA status |
| `/api/brand` | GET | none | brand config |
| `/api/i18n` | GET | none | translations dict |
| `/api/services` | GET | none | services catalogue |
| `/api/pricing` | GET | none | pricing rules |
| `/api/chat` | POST | none | bot turn |
| `/api/chat/poll` | GET | none | live-agent takeover poll |
| `/api/portal/bookings` | GET | phone | customer's bookings |
| `/api/portal/booking/{id}` | GET | none | one booking |
| `/api/portal/quote/{id}` | GET | none | one quote |
| `/api/portal/quote/sign` | POST | none | sign quote, auto-mint invoice |
| `/api/portal/invoice/{id}` | GET | none | one invoice |
| `/api/portal/pay-stub` | POST | none | mark paid (demo) |
| `/api/admin/stats` | GET | bearer | KPIs |
| `/api/admin/bookings` | GET | bearer | list/filter |
| `/api/admin/bookings/{id}/status` | POST | bearer | change status |
| `/api/admin/bookings/{id}/invoice` | POST | bearer | mint invoice |
| `/api/admin/pricing` | GET/POST | bearer | view/override pricing |
| `/api/admin/services` | GET/POST | bearer | view/override services |
| `/api/admin/conversations` | GET | bearer | message log |
| `/api/admin/sessions` | GET | bearer | session list |
| `/api/admin/takeover` | POST | bearer | start takeover |
| `/api/admin/release` | POST | bearer | end takeover |
| `/api/admin/reply` | POST | bearer | inject agent reply |
| `/api/admin/stream` | GET | bearer | SSE event stream |
| `/api/wa/webhook` | POST | bridge token | inbound WhatsApp msg |
| `/api/wa/status` | GET | none | bridge readiness |

## Move into its own repo

```bash
# Fast (no history)
cp -r urbanservices_chatbot /tmp/lumora && cd /tmp/lumora
git init && git add . && git commit -m "Initial commit"
git remote add origin git@github.com:aalmir-erp/lumora.git
git push -u origin main

# With history
git clone <this-repo> lumora && cd lumora
git filter-repo --subdirectory-filter urbanservices_chatbot
git remote add origin git@github.com:aalmir-erp/lumora.git
git push -u origin main
```

Then point Railway at the new repo, drop the `urbanservices_chatbot/` prefix
from `railway.json` paths.

## What's still TODO

- [ ] Real PDF generation (currently the quote view is HTML; print works)
- [ ] WhatsApp media (audio/image) handling
- [ ] Customer push notifications via WhatsApp on status changes
- [ ] Multi-user admin (currently single shared token)
- [ ] Stripe webhook → auto-mark paid (handler stub exists)
- [ ] Recurring booking schedules
- [ ] Loyalty / referral tracking
- [ ] Crew dispatch app (separate service)
