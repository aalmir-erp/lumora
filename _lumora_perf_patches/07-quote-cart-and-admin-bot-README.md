# Patch 07 — Multi-service quote cart + signing + admin bot variant

Fixes the bot reply you saw (just a `/book.html` link with the 4 services
in text) by replacing it with a real itemized cart + signing link + pay
link. Also bumps prices 40%, adds a `/q/{id}` customer signing page,
adds a `/p/{id}` payment page, and adds a separate admin-side bot
behaviour that respects pricing overrides + shows internal margins.

## What's in this patch

| File | Change |
|---|---|
| `app/data/pricing.json` | All `base_per_bedroom`, `min_charge`, `hourly_rate`, etc. multiplied by 1.40 |
| `app/llm.py` | Customer prompt now demands itemized cart format with 3 links. Admin prompt now has full quote-builder protocol with margin display. |
| `app/tools.py` | New tool `create_multi_quote(services[], customer_name, phone, address, target_date, time_slot, notes)` — returns `quote_id`, line items with prices, subtotal, VAT, total, `signing_url`, `pay_url`, fallback contact. |
| `app/multi_quote_pages.py` | New module — `/q/{id}` (signing page with phone gate, signature pad, comments), `/p/{id}` (pay page), `/api/q/{id}/verify`, `/api/q/{id}`, `/api/q/{id}/sign`. Phone-gated access via short HMAC token. |
| `app/main.py` | Registers `_mqp.public_router`. |

## How the customer experience changes

### Before
> 📋 Booking summary
> • Services: Deep Cleaning, Pest Control, Sofa & Carpet…
> • Estimated Total: AED 815
> [Book now →]  ← just a link to /book.html

### After (with patch applied)
> 📋 Quote Q-A1B2C3 (also sent to your phone)
>
> 1. Deep Cleaning — 1 BR, 6 hr     AED 686
> 2. Pest Control — full apartment  AED 490
> 3. Sofa & Carpet — 3-seater + 5x5m AED 392
> 4. Curtain Clean — 4 panels       AED 280
>
> Subtotal:                AED 1,848
> VAT 5%:                   AED  92
> **Total:                AED 1,940**
>
> 📅 Tue, 21 May · 8:00 AM
> 📍 Furjan, Bldg 2327 · Khaqan · 0559396459
>
> ➜ Approve & sign: https://servia.ae/q/Q-A1B2C3
> ➜ Pay online:    https://servia.ae/p/Q-A1B2C3
> ➜ Or pay manually: WhatsApp +971 56 4020087 with the quote number.

Customer taps the signing link → enters their phone (gate) → sees the
itemized cart → signs with finger → adds optional notes → tap **Approve**.
Quote is signed. Admin gets a notification. Customer is taken to the pay
page.

## How the admin experience changes

### Admin chat with bot

> Admin: "Make a quote for Khaqan 0559396459, Furjan, Tue 8AM —
>         deep clean 1BR, pest, sofa 3 seater, curtain 4 panels.
>         Add 15% rush surcharge."
>
> Bot: "Got it. Here's the breakdown:
>      
>      Deep Cleaning 1BR     retail AED 490 · vendor AED 320 · margin AED 170 (35%)
>      Pest Control full     retail AED 350 · vendor AED 200 · margin AED 150 (43%)
>      Sofa & Carpet 3 seat  retail AED 280 · vendor AED 160 · margin AED 120 (43%)
>      Curtain 4 panels      retail AED 200 · vendor AED 100 · margin AED 100 (50%)
>      Subtotal              AED 1,320
>      Rush +15%             AED   198
>      VAT 5%                AED    76
>      Total                 AED 1,594
>      
>      Confirm to generate quote, or say 'change X to Y'?"
>
> Admin: "Confirm and send to customer too"
>
> Bot: "✅ Quote Q-X8Y9Z0 generated.
>      Sent to 0559396459 via WhatsApp.
>      Signing: https://servia.ae/q/Q-X8Y9Z0
>      Pay:     https://servia.ae/p/Q-X8Y9Z0"

Admin can also say "+15%", "-50", "set 1500", "discount 10%", "rush" — all
of these are recognised as pricing overrides for that session only. The
final customer reply NEVER shows margins or vendor cost.

## Apply

In a new lumora-authorised Claude session:

```bash
git apply _lumora_perf_patches/07-quote-cart-and-admin-bot.patch
git add -A && git commit -m "feat(quotes): multi-service cart + signing + admin bot variant + 40% price bump"
git push origin main
```

Wait ~2 min for Railway redeploy. Then test:

1. Open servia.ae chat → ask for "deep clean + pest control + sofa for tomorrow morning"
2. Bot now produces an itemized cart with `Q-XXXXXX`
3. Tap the signing link → phone gate → see the cart → sign → approve
4. Admin gets WhatsApp notification (when bridge is paired)

## Notes / known gaps

- **Stripe checkout button** on `/p/{id}` is currently a placeholder
  (`alert(...)`). Wire it via your existing `/api/webhooks/stripe` path
  when ready.
- **Photo / video upload after service** is NOT in this patch — that's
  Phase 2 (customer comments per line item, vendor uploads, compressed
  upload). Will do in next patch if you confirm priority.
- **Vendor cost / margin numbers** displayed in admin chat are
  illustrative — real numbers come from KB.vendor_data which currently
  only has 100 vehicle-recovery vendors. We'd need to expand the cost
  catalog for cleaning / pest / etc.
- **The 40% price bump applies to all numeric price-like fields in
  pricing.json**. If you wanted to bump only specific services, edit
  `pricing.json` after applying — admin can change live via admin panel
  without redeploy if pricing-override UI exists.

## Next phases (push when ready)

- **Phase 2**: per-line-item approve/reject + comment, photo/video upload
- **Phase 3**: real Stripe checkout on /p/{id} + receipt page
- **Phase 4**: status timeline on /q/{id} (dispatched → arrived → in-progress → done)
