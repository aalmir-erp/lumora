# Lumora E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-03T13:49:21.242790Z
**Result:** **19/20 scenarios passed**


## ❌ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat | None | 30291ms | text len=0, has AED: False, has tool_call: False |

## ✅ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (with addons) | 200 | 5949ms | total: 740.0 AED |

## ✅ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (coverage) | 200 | 5051ms | Sharjah covered: True |

## ✅ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/services | 200 | 394ms | 23 services |
| ✓ GET /api/brand | 200 | 286ms | phone: +971 56 4020087 |
| ✓ GET /api/i18n | 200 | 294ms | 4 languages |

## ✅ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (book) | 200 | 368ms | booking_id: LM-78FB58 |

## ✅ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (AC book) | 200 | 340ms | booking_id: LM-4B24C9 |

## ✅ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/customer/start | 200 | 304ms | OTP: 587559 |
| ✓ POST /auth/customer/verify | 200 | 328ms | customer_id=2, token len=46 |

## ✅ #8: Customer: update profile (name, email, language)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/profile | 200 | 282ms | {"ok": true} |

## ✅ #9: Customer: add 2 saved addresses, fetch list
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/addresses (Home) | 200 | 369ms | id=15 |
| ✓ POST /me/addresses (Office) | 200 | 301ms | null |
| ✓ GET /me/addresses | 200 | 289ms | count=16 |

## ✅ #10: Customer: fetch own bookings
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/me/bookings | 200 | 386ms | count=16 |

## ✅ #11: Customer: cancel a booking with reason
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-78FB58/cancel | 200 | 307ms | {"ok": true} |

## ✅ #12: Customer: reschedule a booking
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-4B24C9/reschedule | 200 | 305ms | to 2026-05-08 16:00 |

## ✅ #13: Customer: submit review (4 stars)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/review | 200 | 296ms | {"ok": true} |

## ✅ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/vendor/login | 200 | 335ms | vendor_id=1, token len=46 |

## ✅ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /vendor/jobs/available | 200 | 277ms | 1 available, first: LM-F5B79E |

## ✅ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /vendor/jobs/claim | 200 | 311ms | {"ok": true, "assignment_id": 5, "payout_amount": 192.0} |
| ✓ POST /vendor/jobs/status (in_progress) | 200 | 235ms | null |
| ✓ POST /vendor/jobs/status (completed) | 200 | 310ms | null |

## ✅ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/stats | 200 | 294ms | bookings_today=16, total=18 |
| ✓ GET /admin/vendors | 200 | 359ms | 45 vendors |
| ✓ GET /admin/services-summary | 200 | 285ms | 23 services |

## ✅ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/brand | 200 | 288ms | phone=+971 56 4020087 |
| ✓ POST /admin/brand (no-op) | 200 | 308ms | null |

## ✅ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/service/deep_cleaning | 200 | 289ms | 12 vendors offering |

## ✅ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/reviews/deep_cleaning | 200 | 298ms | count=0, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": "lt_KRySR\u2026",
  "customer_id": 2,
  "address_id": 15,
  "booking_ids": [
    "LM-78FB58",
    "LM-4B24C9"
  ],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": "lt_gtWhR\u2026",
  "vendor_id": 1,
  "claimable_booking": "LM-F5B79E"
}
```