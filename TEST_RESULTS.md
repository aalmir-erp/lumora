# Servia E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-03T20:41:39.479423Z
**Result:** **16/20 scenarios passed**


## ✅ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat | 200 | 3170ms | text len=248, has AED: True, has tool_call: True |

## ✅ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (with addons) | 200 | 967ms | total: 600.0 AED |

## ❌ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (coverage) | None | 30045ms | Sharjah covered: None |

## ✅ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/services | 200 | 39ms | 32 services |
| ✓ GET /api/brand | 200 | 29ms | phone: +971 56 4020087 |
| ✓ GET /api/i18n | 200 | 32ms | 4 languages |

## ❌ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (book) | 502 | 15039ms | booking_id: None |

## ✅ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (AC book) | 200 | 115ms | booking_id: LM-A15261 |

## ✅ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/customer/start | 200 | 69ms | OTP: 810967 |
| ✓ POST /auth/customer/verify | 200 | 61ms | customer_id=2, token len=46 |

## ✅ #8: Customer: update profile (name, email, language)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/profile | 200 | 35ms | {"ok": true} |

## ✅ #9: Customer: add 2 saved addresses, fetch list
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/addresses (Home) | 200 | 66ms | id=19 |
| ✓ POST /me/addresses (Office) | 200 | 48ms | null |
| ✓ GET /me/addresses | 200 | 37ms | count=20 |

## ✅ #10: Customer: fetch own bookings
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/me/bookings | 200 | 52ms | count=19 |

## ✅ #11: Customer: cancel a booking with reason
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-A15261/cancel | 200 | 68ms | {"ok": true} |

## ❌ #12: Customer: reschedule a booking
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | missing prereqs |

## ✅ #13: Customer: submit review (4 stars)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/review | 200 | 51ms | {"ok": true} |

## ✅ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/vendor/login | 200 | 81ms | vendor_id=1, token len=46 |

## ✅ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /vendor/jobs/available | 200 | 37ms | 0 available, first: None |

## ❌ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no claimable booking |

## ✅ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/stats | 200 | 33ms | bookings_today=19, total=21 |
| ✓ GET /admin/vendors | 200 | 36ms | 45 vendors |
| ✓ GET /admin/services-summary | 200 | 46ms | 32 services |

## ✅ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/brand | 200 | 33ms | phone=+971 56 4020087 |
| ✓ POST /admin/brand (no-op) | 200 | 70ms | null |

## ✅ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/service/deep_cleaning | 200 | 35ms | 12 vendors offering |

## ✅ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/reviews/deep_cleaning | 200 | 34ms | count=0, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": "lt_SddmZ\u2026",
  "customer_id": 2,
  "address_id": 19,
  "booking_ids": [
    "LM-A15261"
  ],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": "lt_lnhix\u2026",
  "vendor_id": 1,
  "claimable_booking": null
}
```