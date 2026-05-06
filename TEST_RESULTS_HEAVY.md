# E2E Heavy Test Results

- ✅ Pass: 40
- ⚠️ Warn: 1
- ❌ Fail: 9
- ⏭ Skip: 0

## Items

- ✅ **[T01] Homepage loads (desktop)** — "Servia: UAE home services in 60 sec · NFC tap-to-book · Cleaning, AC, Recovery"
- ✅ **[T02] Homepage loads (mobile)** — iPhone 12
- ❌ **[T03] /services.html lists services** — exception: only 0 cards
- ✅ **[T04] /coverage.html renders** — OK
- ✅ **[T05] /blog index loads** — OK
- ❌ **[T06] Sitemap has /nfc.html** — exception: nfc.html missing
- ✅ **[T07] robots.txt accessible** — OK
- ✅ **[T08] /faq.html FAQPage schema** — present
- ✅ **[T09] Homepage Org/LocalBusiness schema** — present
- ✅ **[T10] Theme-color is teal #0F766E** — #0F766E
- ❌ **[T11] Mobile nav single-row** — exception: locator.boundingBox: Timeout 18000ms exceeded.
Call log:
  - waiting for locator('.nav-inner img').first()

- ✅ **[T12] Topbanner placeholder bg teal** — OK
- ✅ **[T13] Install banner single row height** — 36px
- ✅ **[T14] Footer present** — OK
- ❌ **[T15] /install.html APK card** — exception: no apk-download
- ❌ **[T16] /install.html Wear OS card** — exception: no wear-download
- ✅ **[T17] /install.html iOS section** — OK
- ✅ **[T18] Search input has ss-input class** — ss-input
- ✅ **[T19] Search trending chips load** — 16 chips
- ✅ **[T20] Hero rotator present** — present
- ✅ **[T21] /nfc.html loads** — OK
- ✅ **[T22] /nfc.html 3-mode panel** — OK
- ✅ **[T23] /nfc.html bot widget** — OK
- ✅ **[T24] /nfc.html bulk-order section** — OK
- ✅ **[T25] /nfc.html schema set** — HowTo+FAQ+Product
- ✅ **[T26] /api/nfc/tag bad slug 404** — OK
- ✅ **[T27] /t/<bad-slug> redirects** — /nfc-not-found.html?slug=zzzzbogus99
- ✅ **[T28] /nfc.html vehicle recovery section** — OK
- ✅ **[T29] /api/nfc/consult endpoint** — greets
- ✅ **[T30] /api/admin/nfc/stats auth-gated** — 401
- ✅ **[T31] /login.html renders** — OK
- ❌ **[T32] /me.html requires auth** — exception: url=https://servia.ae/
- ✅ **[T33] Demo customer login (test@servia.ae)** — lt_GgQ1eZ-TJ...
- ✅ **[T34] Demo customer (aisha@demo)** — OK
- ✅ **[T35] Bad password rejected** — 401 OK
- ✅ **[T36] /api/wallet/balance auth-gated** — 401
- ❌ **[T37] Wallet balance after login** — exception: HTTP 502
- ❌ **[T38] /api/me/bookings authed** — exception: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
- ❌ **[T39] /api/nfc/my-tags authed** — exception: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
- ✅ **[T40] /admin.html responds** — OK
- ✅ **[T41] /api/health responds** — v1.24.3
- ✅ **[T42] /api/services >=10** — 32
- ✅ **[T43] /api/app/latest works** — apk_v=1.24.2
- ✅ **[T44] /api/site/social works** — OK
- ✅ **[T45] /api/brand works** — OK
- ✅ **[T46] /book.html renders form** — OK
- ✅ **[T47] /book.html?service=deep_cleaning prefills** — prefilled
- ✅ **[T48] /book.html?nfc=<bogus> graceful** — OK
- ✅ **[T49] /cart.html loads** — OK
- ⚠️ **[T50] Service worker active** — not registered
