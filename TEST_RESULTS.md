# Servia E2E Test Report

**URL:** https://lumora-production-4071.up.railway.app
**Run at:** 2026-05-15T19:53:29.944010Z
**Result:** **0/20 scenarios passed**


## ❌ #1: Anonymous: deep clean 2BR quote
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat | 404 | 173ms | text len=0, has AED: False, has tool_call: False |

## ❌ #2: Anonymous: deep clean 3BR with addons (oven, fridge)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (with addons) | 404 | 149ms | total: None AED — err: {"status": "error", "code": 404, "message": "Application not found", "request_id": "ee_UXcoBSxeBY |

## ❌ #3: Anonymous: coverage check Sharjah
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (coverage) | 404 | 163ms | Sharjah covered: None |

## ❌ #4: Public: GET /api/services + /api/brand + /api/i18n
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ GET /api/services | 404 | 152ms | 0 services |
| ✗ GET /api/brand | 404 | 154ms | phone: None |
| ✗ GET /api/i18n | 404 | 143ms | 4 languages |

## ❌ #5: Anonymous: book general cleaning 2BR via chat
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (book) | 404 | 133ms | booking_id: None |

## ❌ #6: Anonymous: book AC cleaning 4 units
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /api/chat (AC book) | 404 | 156ms | booking_id: None |

## ❌ #7: Customer: OTP request + verify (login flow)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ OTP issue | 404 | 148ms | no dev_otp returned (WhatsApp bridge active or production mode) |

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

## ❌ #14: Vendor: login (seeded JustMop)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ POST /auth/vendor/login | 404 | 146ms | vendor_id=None, token len=0 |

## ❌ #15: Vendor: list available marketplace jobs
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no vendor token |

## ❌ #16: Vendor: claim a job + mark in_progress + completed
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ skip | — | ?ms | no claimable booking |

## ❌ #17: Admin: GET stats + vendors + services-summary
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ GET /admin/stats | 404 | 146ms | bookings_today=None, total=None |
| ✗ GET /admin/vendors | 404 | 133ms | 0 vendors |
| ✗ GET /admin/services-summary | 404 | 153ms | 0 services |

## ❌ #18: Admin: read brand, no-op patch (preserve existing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ GET /admin/brand | 404 | 145ms | phone=None |
| ✗ POST /admin/brand (no-op) | 404 | 138ms | null |

## ❌ #19: Admin: service detail (vendors + pricing)
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ GET /admin/service/deep_cleaning | 404 | 151ms | 0 vendors offering |

## ❌ #20: Public: GET /api/reviews/deep_cleaning
| Step | Code | Time | Result |
|---|---|---|---|
| ✗ GET /api/reviews/deep_cleaning | 404 | 156ms | count=None, avg=None |

## State captured during run
```json
{
  "phone": "+971501234567",
  "session_id": null,
  "customer_token": null,
  "customer_id": null,
  "address_id": null,
  "booking_ids": [],
  "quote_id": null,
  "invoice_id": null,
  "vendor_token": null,
  "vendor_id": null,
  "claimable_booking": null
}
```