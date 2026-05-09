# Patch 08 — Quote complete experience (per-line approve, photos, status, invoice, real Stripe)

Builds on Patch 07. Adds everything that was Phase 2/3/4:

| What you asked for | Done in this patch |
|---|---|
| Per-service approve / reject + comment | ✅ Each line has Approve/Reject buttons + comment textarea |
| Status timeline visible to customer | ✅ Real-time status events with timestamps |
| Vendor / customer photo + video upload (compressed) | ✅ Client-side JPEG compression (1200px / quality 0.72), video size warning, lightbox viewer |
| Real Stripe checkout on /p/{id} | ✅ Hosted Stripe Checkout Session, AED line items, returns hosted URL |
| Invoice PDF page | ✅ /i/{id} print-friendly, "Print / Save as PDF" button |
| Customer push notif on status change | ✅ send_to_phone() helper hooked into admin status updates |
| Mention features on quote/invoice | ✅ Footer text on /q and /i explains the system |

## New file
- `app/multi_quote_pages.py` — completely rewritten (~580 lines), replaces patch 07's version

## Changed files
- `app/main.py` — admin router registered + Stripe webhook hooks `mark_paid` for multi_quotes
- `app/push_notifications.py` — added `send_to_phone(phone, title, body, url, kind)` helper

## New endpoints

### Customer-side (token-gated)
| Method | Path | Purpose |
|---|---|---|
| GET | `/q/{id}` | signing page with photos, per-line approve, status timeline |
| POST | `/api/q/{id}/verify` | phone gate → token |
| GET | `/api/q/{id}` | full quote data + history + photos |
| POST | `/api/q/{id}/sign` | signature + per-line approvals + customer note |
| POST | `/api/q/{id}/upload` | upload photo/video |
| GET | `/api/q/{id}/photo/{pid}?t=token` | serve a photo |
| GET | `/p/{id}` | payment page (Stripe + WA) |
| POST | `/api/p/{id}/checkout` | create Stripe Checkout session |
| GET | `/i/{id}` | print-friendly invoice |

### Admin-side (ADMIN_TOKEN)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/admin/quote/{id}/status` | dispatched/arrived/in_progress/done/paid |
| POST | `/api/admin/quote/{id}/line-status` | per-line vendor status |
| POST | `/api/admin/quote/{id}/upload` | vendor photo/video upload |
| GET | `/api/admin/quote/{id}/all` | full data + history + photos for admin UI |

## How the customer flow works now

1. Bot generates quote with `create_multi_quote` → returns `Q-XXXXXX`
2. Customer taps `/q/Q-XXXXXX` → enters phone → sees full cart
3. Customer taps **Approve** or **Reject** per line, types comments
4. Customer signs with finger
5. Customer taps **Approve all & sign**
6. Quote signed → admin gets notification → status="signed"
7. Customer can pay via card (Stripe), WhatsApp, or view invoice
8. Vendor team uploads service photos → status updates → push to customer's phone
9. Photos appear on `/q/{id}` for customer to view (lightbox)
10. After service: status="done" → push notif → invoice marked PAID after Stripe webhook

## Stripe setup

Patch is **graceful** — if `STRIPE_SECRET_KEY` env var is not set on
Railway, the "Pay with card" button is disabled with a hint. Set it:

1. Stripe dashboard → Developers → API keys → Reveal Live secret key
2. Railway → Variables → `STRIPE_SECRET_KEY` = `sk_live_...`
3. Set webhook on Stripe dashboard → endpoint `https://servia.ae/api/webhooks/stripe` → event `checkout.session.completed`
4. Add `STRIPE_WEBHOOK_SECRET` env (the signing secret from the webhook endpoint)

After that, real card payments work end-to-end.

## Apply

```bash
git apply _lumora_perf_patches/08-quote-complete-experience.patch
git add -A && git commit -m "feat(quotes): per-line approve+comment, photos, status timeline, real Stripe, invoice"
git push origin main
```

## Test plan

After Railway redeploys (~2 min):

1. Generate a quote via chat: "deep clean + pest + sofa"
2. Open the `/q/Q-XXXXXX` link as customer → enter phone → see new UI
3. Approve some lines, reject one, add a comment, sign, hit Approve
4. Open admin panel → see push notification + admin alert
5. Hit `/api/admin/quote/{id}/status` with `{"status":"dispatched"}` to push status update
6. Customer's quote page now shows updated status + timeline
7. As admin, upload a photo via `/api/admin/quote/{id}/upload`
8. Customer reloads → sees photo in the photos section

## Total lines in patch 08
~1,000 lines

## Cumulative patch count
8 patches, 17 files, ~5,500 insertions.
