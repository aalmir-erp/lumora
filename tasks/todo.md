# Servia Roadmap — TODO Checklist

Source: `/root/.claude/plans/snuggly-churning-lantern.md`
Read at session start.

---

## Slice A — E2E Live Viewer + "Run Now" button (v1.24.89)

- [x] Backend: `GET /api/admin/e2e/runs?limit=N` — proxy GitHub list-runs API
- [x] Backend: `GET /api/admin/e2e/run/{id}/jobs` — proxy GitHub jobs API
- [x] Frontend: `web/admin-e2e-shots.html` — add 🚀 Run-now button
- [x] Frontend: live status row with auto-refresh (10s while in_progress)
- [x] Frontend: confirmation modal before triggering
- [ ] Push v1.24.89, tag, watch workflow, verify thumbnail commit-back
- [ ] **Stop condition**: confirm UX with user before Slice B

---

## Slice A.5 — Sitewide Pin-First Address Card (v1.24.90, URGENT)

- [ ] Widget: extract `[[picker:address]]` marker, render address card inline
- [ ] Widget: on submit, send structured JSON as user message + auto-save to profile
- [ ] Bot prompt: strict rule — NEVER ask address as free text; always emit picker
- [ ] Bot post-processor: if reply contains "share the full address" / "could you provide the address" patterns, auto-inject `[[picker:address]]`
- [ ] /book.html — replace free-text address input with card
- [ ] /cart.html — same
- [ ] Backend: `POST /api/me/locations/upsert-from-pin` (dedupe within 30m)
- [ ] Anonymous-session bridge: stash address in sessionStorage; backfill on auth
- [ ] Saved-places dropdown (top of card) — populated from `/api/me/profile.locations`
- [ ] Tests: `tests/test_address_card_e2e.py` (10+ scenarios with VERBATIM v1.24.88 screenshot text)
- [ ] Append to `tests/test_real_fixtures.py`
- [ ] Visual proof: screenshot the chat showing card rendered in-place
- [ ] Bumped version, pushed, Playwright green
- [ ] Lesson L9 added to `tasks/lessons.md`

---

## Slice B — Recurring Scheduler Foundation (v1.24.91)

- [ ] Schema: `schedules` + `schedule_items` + `schedule_recurrence` +
      `schedule_reminders` + `schedule_occurrences` +
      `ai_schedule_suggestions` (idempotent ALTER/CREATE)
- [ ] Module: `app/scheduler_recurring.py` — RRULE parser + materialiser
- [ ] APIs: 7 endpoints under `/api/me/schedules/*`
- [ ] Cron: `_job_materialise` daily at 03:00 Asia/Dubai
- [ ] Tests: `tests/test_scheduler_recurring.py` — 25 scenarios
- [ ] All 144 existing tests still pass
- [ ] Push v1.24.90, watch Playwright (no UI yet, just smoke)

---

## Slice C — Scheduler Wizard UI + Calendar (v1.24.91)

- [ ] Page: `web/me-schedule.html` — 5-step wizard + month calendar
- [ ] AI suggestion banner (uses Claude for cadence)
- [ ] RRULE builder modal for "Custom" repeat
- [ ] Bottom-sheet: Skip / Reschedule / Cancel-future / Specialist
- [ ] Link from `/me-profile` settings tab
- [ ] Playwright tests T51–T55 for the wizard
- [ ] **Stop condition**: confirm wizard feels right before Slice D

---

## Slice D — Auto-charge Cron + Reminders (v1.24.92)

- [ ] Cron: `_job_remind` hourly :15
- [ ] Cron: `_job_charge` hourly :45
- [ ] Wallet debit helper (extend `app/nfc.py` if needed)
- [ ] Auto-pause-while-traveling: `paused_traveling` status
- [ ] WhatsApp-skip via bridge webhook
- [ ] No-show refund cron (24h post-occurrence)
- [ ] Tests: `tests/test_scheduler_charge.py`

---

## Slice E — Airbnb iCal Turnover (v1.24.93)

- [ ] Add `icalendar>=5.0` to `requirements.txt`
- [ ] Schema: `properties` + `property_calendars` + `property_overrides`
- [ ] Module: `app/airbnb_turnover.py` — iCal poller + occurrence creator
- [ ] APIs: 5 endpoints under `/api/me/properties/*`
- [ ] Cron: `_job_poll_ical` every 4h
- [ ] Test fixture: `tests/fixtures/sample-airbnb.ics`
- [ ] Tests: `tests/test_airbnb_turnover.py`
- [ ] **Stop condition**: confirm iCal flow is correct before Slice F

---

## Slice F — Turnover UI + Marketing (v1.24.94)

- [ ] Page: `web/me-properties.html` — host dashboard
- [ ] Route: `/services/airbnb-hosts` (canonical service.html template)
- [ ] Update `app/main.py::llms_txt` — add 2 new sections
- [ ] Update `web/banner.js` — new hero rotation slide
- [ ] Add-on services: `linen_rental`, `welcome_basket`, `pre_arrival_check`
- [ ] Playwright tests T56–T60
- [ ] Final review + 100% green run on Playwright

---

## Cross-cutting

- [ ] Mirror Operating Contract into `CLAUDE.md` Working Instructions
      (so future sessions inherit it)
- [ ] Bump version each push (1.24.89 → 1.24.94)
- [ ] Cache-bust `?v=` in all HTML files per push
- [ ] Trigger Playwright after each push (tag + workflow_dispatch)
- [ ] Visual review 2-3 screenshots per slice before declaring done

---

## Results section (filled as slices complete)

### Slice A — _pending_
### Slice B — _pending_
### Slice C — _pending_
### Slice D — _pending_
### Slice E — _pending_
### Slice F — _pending_
