# Servia E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-04T08:42:51.959131Z
**Result:** **13/20 scenarios passed**


## ✅ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat | 200 | 516ms | text len=248, has AED: True, has tool_call: True |

## ✅ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (with addons) | 200 | 341ms | total: 600.0 AED |

## ✅ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (coverage) | 200 | 262ms | Sharjah covered: True |

## ✅ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/services | 200 | 391ms | 32 services |
| ✓ GET /api/brand | 200 | 187ms | phone: +971 56 4020087 |
| ✓ GET /api/i18n | 200 | 250ms | 15 languages |

## ✅ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (book) | 200 | 344ms | booking_id: LM-800277 |

## ✅ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /api/chat (AC book) | 200 | 261ms | booking_id: LM-5826AC |

## ❌ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ OTP issue | 200 | 231ms | no dev_otp returned (WhatsApp bridge active or production mode) |

## ❌ #8: Customer: update profile (name, email, language)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no token |

## ❌ #9: Customer: add 2 saved addresses, fetch list
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no token |

## ❌ #10: Customer: fetch own bookings
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no token |

## ❌ #11: Customer: cancel a booking with reason
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | missing prereqs |

## ❌ #12: Customer: reschedule a booking
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | missing prereqs |

## ❌ #13: Customer: submit review (4 stars)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no booking |

## ✅ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /auth/vendor/login | 200 | 234ms | vendor_id=1, token len=46 |

## ✅ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /vendor/jobs/available | 200 | 205ms | 1 available, first: LM-800277 |

## ✅ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ POST /vendor/jobs/claim | 200 | 210ms | {"ok": true, "assignment_id": 7, "payout_amount": 192.0} |
| ✓ POST /vendor/jobs/status (in_progress) | 200 | 223ms | null |
| ✓ POST /vendor/jobs/status (completed) | 200 | 208ms | null |

## ✅ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/stats | 200 | 194ms | bookings_today=13, total=34 |
| ✓ GET /admin/vendors | 200 | 179ms | 45 vendors |
| ✓ GET /admin/services-summary | 200 | 253ms | 32 services |

## ✅ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/brand | 200 | 184ms | phone=+971 56 4020087 |
| ✓ POST /admin/brand (no-op) | 200 | 215ms | null |

## ✅ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /admin/service/deep_cleaning | 200 | 180ms | 12 vendors offering |

## ✅ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✓ GET /api/reviews/deep_cleaning | 200 | 183ms | count=0, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": null,
  "customer_id": null,
  "address_id": null,
  "booking_ids": [
    "LM-800277",
    "LM-5826AC"
  ],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": "lt__OQep\u2026",
  "vendor_id": 1,
  "claimable_booking": "LM-800277"
}
```