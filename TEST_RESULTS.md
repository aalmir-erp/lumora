# Lumora E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-03T04:12:50.076652Z
**Result:** **18/20 scenarios passed**


## ✅ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat | 200 | 7490ms | text len=409, has AED: True, has tool_call: True |

## ✅ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (with addons) | 200 | 10386ms | total: 600.0 AED |

## ✅ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (coverage) | 200 | 4503ms | Sharjah covered: True |

## ✅ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/services | 200 | 458ms | 23 services |
| ✓ GET /api/brand | 200 | 292ms | phone: +971 56 4020087 |
| ✓ GET /api/i18n | 200 | 292ms | 4 languages |

## ✅ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (book) | 200 | 27622ms | booking_id: LM-428CC3 |

## ❌ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (AC book) | None | 30136ms | booking_id: None |

## ✅ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/customer/start | 200 | 328ms | OTP: 158149 |
| ✓ POST /auth/customer/verify | 200 | 256ms | customer_id=2, token len=46 |

## ✅ #8: Customer: update profile (name, email, language)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/profile | 200 | 278ms | {"ok": true} |

## ✅ #9: Customer: add 2 saved addresses, fetch list
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/addresses (Home) | 200 | 302ms | id=5 |
| ✓ POST /me/addresses (Office) | 200 | 321ms | null |
| ✓ GET /me/addresses | 200 | 293ms | count=6 |

## ✅ #10: Customer: fetch own bookings
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/me/bookings | 200 | 302ms | count=5 |

## ✅ #11: Customer: cancel a booking with reason
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-428CC3/cancel | 200 | 311ms | {"ok": true} |

## ❌ #12: Customer: reschedule a booking
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | missing prereqs |

## ✅ #13: Customer: submit review (4 stars)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/review | 200 | 305ms | {"ok": true} |

## ✅ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/vendor/login | 200 | 343ms | vendor_id=1, token len=46 |

## ✅ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /vendor/jobs/available | 200 | 288ms | 1 available, first: LM-80D201 |

## ✅ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /vendor/jobs/claim | 200 | 315ms | {"ok": true, "assignment_id": 3, "payout_amount": 160.0} |
| ✓ POST /vendor/jobs/status (in_progress) | 200 | 241ms | null |
| ✓ POST /vendor/jobs/status (completed) | 200 | 365ms | null |

## ✅ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/stats | 200 | 218ms | bookings_today=5, total=7 |
| ✓ GET /admin/vendors | 200 | 337ms | 45 vendors |
| ✓ GET /admin/services-summary | 200 | 368ms | 23 services |

## ✅ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/brand | 200 | 295ms | phone=+971 56 4020087 |
| ✓ POST /admin/brand (no-op) | 200 | 324ms | null |

## ✅ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/service/deep_cleaning | 200 | 222ms | 12 vendors offering |

## ✅ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/reviews/deep_cleaning | 200 | 221ms | count=0, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": "lt_bPEfN\u2026",
  "customer_id": 2,
  "address_id": 5,
  "booking_ids": [
    "LM-428CC3"
  ],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": "lt_yaKus\u2026",
  "vendor_id": 1,
  "claimable_booking": "LM-80D201"
}
```