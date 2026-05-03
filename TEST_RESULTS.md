# Lumora E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-03T00:15:54.914434Z
**Result:** **18/20 scenarios passed**


## ✅ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat | 200 | 7087ms | text len=480, has AED: True, has tool_call: True |

## ❌ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (with addons) | 502 | 5209ms | total: None AED |

## ❌ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ exception | — | ?ms | "'NoneType' object is not subscriptable" |

## ✅ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/services | 200 | 153ms | 23 services |
| ✓ GET /api/brand | 200 | 238ms | phone: +971 56 4020087 |
| ✓ GET /api/i18n | 200 | 94ms | 4 languages |

## ✅ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (book) | 200 | 11307ms | booking_id: LM-A7AC2C |

## ✅ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (AC book) | 200 | 15531ms | booking_id: LM-9F76F5 |

## ✅ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/customer/start | 200 | 99ms | OTP: 802175 |
| ✓ POST /auth/customer/verify | 200 | 104ms | customer_id=2, token len=46 |

## ✅ #8: Customer: update profile (name, email, language)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/profile | 200 | 79ms | {"ok": true} |

## ✅ #9: Customer: add 2 saved addresses, fetch list
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/addresses (Home) | 200 | 94ms | id=3 |
| ✓ POST /me/addresses (Office) | 200 | 86ms | null |
| ✓ GET /me/addresses | 200 | 84ms | count=4 |

## ✅ #10: Customer: fetch own bookings
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/me/bookings | 200 | 83ms | count=3 |

## ✅ #11: Customer: cancel a booking with reason
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-A7AC2C/cancel | 200 | 109ms | {"ok": true} |

## ✅ #12: Customer: reschedule a booking
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /me/booking/LM-9F76F5/reschedule | 200 | 98ms | to 2026-05-08 16:00 |

## ✅ #13: Customer: submit review (4 stars)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/me/review | 200 | 90ms | {"ok": true} |

## ✅ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/vendor/login | 200 | 130ms | vendor_id=1, token len=46 |

## ✅ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /vendor/jobs/available | 200 | 128ms | 2 available, first: LM-802C2C |

## ✅ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /vendor/jobs/claim | 200 | 104ms | {"ok": true, "assignment_id": 2, "payout_amount": 68.0} |
| ✓ POST /vendor/jobs/status (in_progress) | 200 | 101ms | null |
| ✓ POST /vendor/jobs/status (completed) | 200 | 106ms | null |

## ✅ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/stats | 200 | 77ms | bookings_today=3, total=5 |
| ✓ GET /admin/vendors | 200 | 81ms | 45 vendors |
| ✓ GET /admin/services-summary | 200 | 78ms | 23 services |

## ✅ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/brand | 200 | 80ms | phone=+971 56 4020087 |
| ✓ POST /admin/brand (no-op) | 200 | 127ms | null |

## ✅ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/service/deep_cleaning | 200 | 86ms | 12 vendors offering |

## ✅ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/reviews/deep_cleaning | 200 | 80ms | count=0, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": "lt_nO3CX\u2026",
  "customer_id": 2,
  "address_id": 3,
  "booking_ids": [
    "LM-A7AC2C",
    "LM-9F76F5"
  ],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": "lt_LMavT\u2026",
  "vendor_id": 1,
  "claimable_booking": "LM-802C2C"
}
```