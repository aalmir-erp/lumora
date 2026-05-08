# Aalmir Plastic — WhatsApp AI Chatbot

A senior-grade WhatsApp chatbot for **aalmirplastic.com**, built on the
official Meta WhatsApp Cloud API with a provider-agnostic AI layer
(Anthropic Claude or OpenAI GPT, switchable at runtime).

The bot:

- talks to WhatsApp customers as a friendly UAE plastic-industry sales engineer
- collects quote requests step-by-step (product, grade, dimensions, qty, delivery, contact)
- saves every order to a database with status workflow (new → contacted → quoted → closed)
- pauses itself for 4 hours after escalating, so a human agent can take over without bot interference
- ships with an **admin panel** at `/admin` for managing tokens, KB, orders, and conversations
- supports prompt caching on Claude for ~10× cost reduction on repeat traffic

## Quick deploy on Railway

1. Click **[Deploy on Railway](https://railway.com/new/template?template=https://github.com/aalmir-erp/whatsapp-ai-chatbot)** (replace with your repo URL after pushing).
2. Set just two env vars:
   - `ADMIN_BOOTSTRAP_TOKEN` — any long random string. You'll paste this once during admin setup.
   - `SESSION_SECRET` — another long random string (cookie signing key).
3. Add a **Railway volume** mounted at `/data` and set env var `DB_PATH=/data/aalmir_bot.db` so your data survives redeploys.
4. Open the deployed URL → it redirects to `/admin/setup`. Set your admin password using the bootstrap token.
5. From the admin panel, go to **Tokens & Keys** and paste each value (Meta access token, phone number ID, app secret, AI provider key). Use the **Where to find them** page if you need help locating each one.

## Wiring to Meta WhatsApp Cloud API

In the Meta App dashboard (developers.facebook.com/apps):

1. **WhatsApp → API Setup**: copy Phone Number ID, Access Token (24h temp is fine for testing), WABA ID.
2. **App Settings → Basic**: copy App Secret.
3. **WhatsApp → Configuration → Webhook**:
   - Callback URL: `https://<your-railway-app>/webhook`
   - Verify Token: any random string you also paste into the admin Tokens page as **Meta Webhook Verify Token**.
   - Subscribe to the `messages` field.

The setup guide page inside the admin panel walks you through all of this.

## Local dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in ADMIN_BOOTSTRAP_TOKEN at minimum
uvicorn app.main:app --reload --port 8000
```

Open <http://localhost:8000/admin> → set admin password → paste tokens.

Use ngrok to expose `/webhook` to Meta during testing:

```bash
ngrok http 8000
```

## Architecture

```
Customer → +971 4 880 2873 → Meta Cloud API ──┬──► /webhook  (signature-verified)
                                              │       ↓
                                              │   AI provider (Claude or GPT)
                                              │       ↓
                                              │   Reply via Cloud API
                                              │
                                              └──► Meta Inbox  (sales agents see threads)
```

When the bot completes a quote intake or escalates:

- Order details are extracted from a structured `<ORDER>...</ORDER>` JSON block in the model's reply
- Saved to the `orders` table → visible at `/admin/orders`
- Sales team is notified via the configured `HANDOFF_WHATSAPP` number
- The conversation is paused for 4h so the bot doesn't talk over the human

## Project layout

```
app/
├── main.py              FastAPI app, webhook + admin routes
├── admin.py             Admin panel routes
├── auth.py              Admin auth (PBKDF2)
├── settings_store.py    Layered settings: env > db > default
├── db.py                SQLite engine + schema
├── orders.py            Order extraction + persistence
├── conversation.py      Per-user history (in-memory, optional Redis)
├── persona.py           Senior-bot system prompt + order intake instructions
├── kb.py                Editable knowledge base
├── whatsapp.py          Meta Cloud API client + signature verification
├── config.py            Env-only settings (pydantic)
├── ai/                  Provider-agnostic AI (Claude / OpenAI)
├── templates/           Jinja2 templates for /admin
└── static/              CSS for /admin
tests/                   Pytest suite
```

## Admin pages

- **Dashboard** — KPIs, health check, webhook URL to paste in Meta
- **Tokens & Keys** — paste/edit every credential the bot needs
- **Where to find them** — exact step-by-step on each token's location in Meta / Anthropic / OpenAI
- **Knowledge Base** — edit the bot's product/FAQ/contact blocks live, no redeploy
- **Orders** — list, filter, status workflow
- **Conversations** — recent chats per WhatsApp number

## Cost estimate

| Volume | Total monthly |
|---|---|
| Pilot (~100 chats/month) | ~$10 |
| Active (~1,000 chats/month) | ~$25–35 |
| Heavy (~10,000 chats/month) | ~$200–250 |

Service-category WhatsApp conversations (customer-initiated, replies
within 24h) are free on Meta. AI cost dominates as volume grows.

## Security notes

- **Always set `ADMIN_BOOTSTRAP_TOKEN` before exposing the URL publicly**, otherwise the first random visitor can claim the admin account.
- Meta webhook signature verification is enforced when `META_APP_SECRET` is set. Don't run prod without it.
- Tokens stored in DB are not encrypted at the application level — rely on your host's disk encryption + restricted DB access.
- Rotate the Meta access token every 60 days. Permanent System User tokens don't expire but should still be rotated yearly.
