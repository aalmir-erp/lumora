# Servia E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-03T19:18:17.922058Z
**Result:** **18/20 scenarios passed**


## ❌ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat | None | 30150ms | text len=0, has AED: False, has tool_call: False |

## ✅ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (with addons) | 200 | 6983ms | total: 740.0 AED |

## ✅ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (coverage) | 200 | 5159ms | Sharjah covered: True |

## ✅ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/services | 200 | 381ms | 23 services |
| ✓ GET /api/brand | 200 | 335ms | phone: +971 56 4020087 |
| ✓ GET /api/i18n | 200 | 361ms | 4 languages |

## ✅ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (book) | 200 | 305ms | booking_id: LM-2342CA |

## ✅ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (AC book) | 200 | 402ms | booking_id: LM-E39586 |

## ✅ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/customer/start | 200 | 318ms | OTP: 514375 |
| ✓ POST /auth/customer/verify | 200 | 279ms | customer_id=2, token len=46 |

## ✅ #8: Customer: update profile (name, email, language)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/profile | 200 | 300ms | {"ok": true} |

## ✅ #9: Customer: add 2 saved addresses, fetch list
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/addresses (Home) | 200 | 305ms | id=17 |
| ✓ POST /me/addresses (Office) | 200 | 274ms | null |
| ✓ GET /me/addresses | 200 | 236ms | count=18 |

## ✅ #10: Customer: fetch own bookings
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/me/bookings | 200 | 356ms | count=18 |

## ✅ #11: Customer: cancel a booking with reason
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-2342CA/cancel | 200 | 284ms | {"ok": true} |

## ✅ #12: Customer: reschedule a booking
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-E39586/reschedule | 200 | 289ms | to 2026-05-08 16:00 |

## ✅ #13: Customer: submit review (4 stars)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/review | 200 | 295ms | {"ok": true} |

## ✅ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/vendor/login | 200 | 299ms | vendor_id=1, token len=46 |

## ✅ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /vendor/jobs/available | 200 | 213ms | 0 available, first: None |

## ❌ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no claimable booking |

## ✅ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/stats | 200 | 259ms | bookings_today=18, total=20 |
| ✓ GET /admin/vendors | 200 | 350ms | 45 vendors |
| ✓ GET /admin/services-summary | 200 | 317ms | 23 services |

## ✅ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/brand | 200 | 284ms | phone=+971 56 4020087 |
| ✓ POST /admin/brand (no-op) | 200 | 303ms | null |

## ✅ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/service/deep_cleaning | 200 | 274ms | 12 vendors offering |

## ✅ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/reviews/deep_cleaning | 200 | 263ms | count=0, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": "lt_jYUcU\u2026",
  "customer_id": 2,
  "address_id": 17,
  "booking_ids": [
    "LM-2342CA",
    "LM-E39586"
  ],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": "lt_t0a9H\u2026",
  "vendor_id": 1,
  "claimable_booking": null
}
```