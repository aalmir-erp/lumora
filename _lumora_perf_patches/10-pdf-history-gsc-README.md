# Patch 10 — Real PDF + History tab + Google Search Console fixes

Three big things in one shot.

## 1. Real PDF generation (`/i/{quote_id}.pdf`)

- Uses `fpdf2` (pure-Python, no system deps, ~500 KB install)
- Endpoint: `GET /i/Q-XXXXXX.pdf` → returns native PDF download
- Includes header band, billing details, itemised table with prices, totals,
  PAID/PENDING stamp, footer note explaining the system
- Falls back to `/i/{id}` HTML print page if `fpdf2` isn't installed
- New "📄 PDF" button added to history tab cards

`requirements.txt` adds `fpdf2>=2.7`. Railway will pip-install on next deploy.

## 2. Chat widget "📜 History" tab

New tab inside the chat widget. Customer enters phone (and optionally email)
→ system finds:
- All quotes / orders (with status, total, view/invoice/PDF/pay buttons)
- All bookings (legacy)
- All invoices (legacy + new)
- All past chat sessions (tap to view conversation in chat tab)

Each card shows:
- **Quotes**: ID, status chip (color-coded), date, services, total, PAID stamp,
  4-button row (View / Invoice / 📄 PDF / Pay)
- **Bookings**: service ID, date, status, address
- **Invoices**: ID, amount, PAID/PENDING
- **Chats**: timestamp, message count, preview (tap to expand into chat tab)

Phone matching is **last 9 digits** so `+971...`, `971...`, `0...` all match.

New backend endpoints:
- `POST /api/me/history` — body `{phone, email}` → returns all matched data
- `GET /api/me/chat/{session_id}?phone=...` — full message history if phone matches

## 3. Google Search Console fixes

Three issues from the GSC emails resolved:

### "Duplicate without user-selected canonical"
8 public pages now have `<link rel="canonical" href="...">` injected into `<head>`:
- `/account.html`, `/booked.html`, `/delivered.html`, `/invoice.html`,
  `/me.html`, `/quote.html`, `/vendor.html`, `/partner-agreement.html`

### "Alternative page with proper canonical tag"
Admin-only / utility pages now have `<meta name="robots" content="noindex,nofollow">`:
- `/admin-live.html`, `/reset.html` (others already had it)

### "Q&A structured data issues" — 5 missing fields
9 HTML files patched (faq.html, index.html, service.html, area.html, nfc*.html).
Added required fields to every `Question` and `Answer` JSON-LD block:
- `Question`: `author` (Organization=Servia), `datePublished` (today), `text`
- `Answer`: `author`, `datePublished`, `upvoteCount: 1`

Done both for static JSON-LD blocks AND the dynamic FAQPage generator in faq.html.

## Apply

```bash
git apply _lumora_perf_patches/10-pdf-history-gsc.patch
git add -A && git commit -m "feat: native PDF invoices, history tab, GSC schema + canonical fixes"
git push origin main
```

After Railway redeploy:

1. **Test PDF**: open `https://servia.ae/i/Q-XXXXXX.pdf` (any signed quote) → should download a clean PDF
2. **Test History**: open chat widget → tap "📜 History" tab → enter your phone → see your past records
3. **Verify GSC fixes** (give it 2–3 days for Google to recrawl):
   - Search Console → Coverage report → "Duplicate without canonical" count drops
   - Schema → Q&A → "Missing field" warnings clear

## Total lines
2,169 lines (largest patch yet — covers a lot of HTML).

## Cumulative
10 patches, ~7,800 insertions.

## What's now COMPLETE from the entire session

✅ Page perf optimizations (defer health check, logo dims, etc.)
✅ Admin number scrub (3 patches)
✅ Traffic source parsing
✅ Admin Live PWA (visitors + chats + push + watch mirror)
✅ AI Arena always wins
✅ Multi-service quote cart
✅ Per-line approve, photos, status, Stripe, invoice
✅ Chat widget controls (min/max/download/new chat) + persistence
✅ Real PDF generation
✅ Customer history tab
✅ Google Search Console issues (canonical + Q&A schema)

## Still TODO (not in any patch yet)

- WhatsApp bridge fix (need Railway logs from you to diagnose)
- Watch face faces (Galaxy Store / Play Internal Testing)

Both depend on inputs from you (logs, Play Console verification, Galaxy Store
Watch Faces permission email).
