# Patch 11 — Click-trail, tool-call hints, quote management UI, WA bridge auto-recovery

Wraps up the remaining "phase 1 / phase 2 nice-to-haves" from earlier in
the session. Four self-contained features in one patch.

## 1. Live visitor click-trail

`app/live_visitors.py`:
- New table `visitor_pageviews` — every page hit logged with timestamp
- Insert hooks added to both update + insert paths in `track()`
- New endpoint `GET /api/admin/live/visitor/{vid}/trail?limit=200` →
  visitor's full page history newest-first

So instead of just "last page", admin can now see exactly which pages
the visitor navigated through (e.g. `/` → `/services.html` →
`/book.html?service=ac_cleaning` → `/me.html`). Powers later: "abandoned
cart" detection.

## 2. Bot tool-call hints in admin chat detail

`app/admin_live.py`:
- `chat_messages()` now reads `tool_calls_json` from `conversations` and
  surfaces a parsed summary
- `_summarise()` cherry-picks the most informative field (quote_id,
  booking_id, total_aed, error, etc.) into a one-liner

`web/admin-live.js`:
- Each message in `loadChatDetail()` now shows a blue tool-call card
  beneath the bot reply, e.g. `🛠 create_multi_quote · quote_id=Q-A1B2C3`
- Admin instantly sees what the bot ATTEMPTED to do for any message,
  without diving into the database

## 3. Admin Live PWA — Quotes tab + management

`web/admin-live.html`:
- New tab `Quotes` next to Visitors / Chats with badge counter

`web/admin-live.js`:
- `renderQuotes()` lists last 7 days of quotes with status chip, total,
  customer info
- Tap a quote card → full-screen detail view with:
  - Customer info, address, schedule, services list
  - **Status update buttons**: dispatched / arrived / in_progress / done / cancelled
  - **Photo / video upload** input (uses existing admin_router upload endpoint)
  - Quick links: customer signing page / invoice / PDF

`app/admin_live.py`:
- New endpoint `GET /api/admin/live/quotes/recent?days=7` → list

So admin can manage every active quote without leaving the PWA. Status
changes push live status updates to the customer's phone (via existing
`send_to_phone` + `_add_event` from patch 08).

## 4. WhatsApp bridge graceful degradation

`app/admin_alerts.py`:
- Bridge down (5xx or timeout) → marks bridge unhealthy for 5 min
- All subsequent `notify_admin` calls skip the bridge instantly (no
  8-second wait) until the cooldown expires
- Web Push continues normally during the cooldown — admin still gets
  alerts on phone PWA + watch
- Self-healing: after the cooldown, next call retries the bridge

Result: when your `/qr` page shows "503 — WhatsApp not paired", the rest
of Servia doesn't get bogged down. Push notifications and admin live PWA
keep working.

## Apply

```bash
git apply _lumora_perf_patches/11-trail-tools-quotes-bridge.patch
git add -A && git commit -m "feat: visitor trail, tool-call hints, quote mgmt UI, WA bridge auto-recovery"
git push origin main
```

## Test plan

After Railway redeploys (~2 min):

1. **Click-trail**: visit a few pages on servia.ae, then in admin DB run:
   `SELECT * FROM visitor_pageviews WHERE visitor_id='...' ORDER BY id DESC LIMIT 10;`
   You should see your pages logged.
2. **Tool-call hints**: trigger a quote in chat. In admin-live PWA → Chats
   tab → tap your session → bot's reply now has a blue `🛠 create_multi_quote · quote_id=Q-...` chip below it.
3. **Quote management**: admin-live → Quotes tab → tap any quote → tap a
   status button → customer's `/q/{id}` page reflects the new status
   within 4s.
4. **Bridge degrade**: while WA bridge is down (your current state), open
   the chat widget, send a message. Reply latency should be normal (no
   8s lag waiting for the dead bridge).

## Cumulative

11 patches, 17 files, ~6,800 patch lines.

## What's still TODO (genuinely outside what I can do)

- WhatsApp bridge container fix on Railway (need Railway logs from you)
- Watch face faces (Galaxy Store / Play Internal Testing — your account work)

Both depend on inputs from your side. Patches handle everything else.
