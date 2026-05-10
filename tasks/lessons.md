# Servia Lessons — Pattern Catalog

> Short-form companion to `CLAUDE.md` TESTING LOOPHOLES.
> Read at the start of every session.
> One entry per pattern: **symptom** · **root cause** · **prevention rule**.

---

## L1 — "Tested but failed in production" (DB env-var mismatch)
**Symptom**: 31/31 unit tests pass locally, then production reports a
phantom-data behaviour the tests didn't catch.
**Root cause**: tests set `DATABASE_URL` but the app reads `DB_PATH`.
Tests were silently sharing `/tmp/lumora.db` across runs and accumulating
rows.
**Prevention**:
- `grep -nE "DATABASE_URL|DB_PATH" app/db.py app/config.py` BEFORE writing
  the first test for any new module.
- Always use the actual env-var name the production code reads.
- Pattern: `os.environ["DB_PATH"] = "/tmp/test_<feature>.db"` followed by
  `os.path.exists(...) and os.unlink(...)` BEFORE any `from app import …`.

---

## L2 — "Tested only one fixture format"
**Symptom**: parser passes synthetic test, fails on real LLM output.
**Root cause**: I tested the format I made up; LLM emitted a different
format (✓ inline vs bulleted, em-dash vs hyphen, "Date & Time" vs "Time").
**Prevention**:
- Every text-parser test must include AT LEAST ONE fixture that is the
  EXACT text from the user's most recent screenshot, copy-pasted verbatim.
- Live fixture file: `tests/test_real_fixtures.py` — every "no Q-
  generated" complaint adds a new entry here BEFORE the parser fix.

---

## L3 — "Cloudflare 502 transient looks like real failure"
**Symptom**: live Playwright reports 1–2 page-load failures that don't
reproduce locally.
**Root cause**: Cloudflare cold-load can return 502 once before warming.
**Prevention**:
- Live-site Playwright tests that fetch a page MUST retry once with 1.5s
  backoff before failing.
- Pattern: see `tests/e2e-heavy.mjs` T23/T24.

---

## L4 — "Workflow YAML heredoc broke parsing"
**Symptom**: GitHub Actions reports `total_count: 0 jobs` after a tag
push, run shows status=failure with no executed steps.
**Root cause**: Inline Python heredoc inside `run: |` block scalar started
at column 0; YAML expects indented continuation.
**Prevention**:
- Don't put multi-line heredocs in `run: |` blocks.
- Extract Python into `.scripts/<name>.py` and call it as a single line:
  `python3 .scripts/<name>.py "$ARG"`.
- Validate before push: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/<file>.yml'))"`.

---

## L5 — "Workflow checked out at tag (detached HEAD), couldn't push"
**Symptom**: workflow succeeds but never commits screenshots back to
main.
**Root cause**: tag-push triggers checkout the tag's SHA in detached
HEAD. `git push origin HEAD:main` from detached HEAD with --rebase fails
silently when the remote has moved.
**Prevention**:
- In commit-back step: explicitly `git fetch origin main && git checkout
  -B main origin/main` before staging + committing + pushing.
- Add `set -x` for visibility while debugging workflow steps.

---

## L6 — "Path-prefix shortcut bypassed the rewrite step"
**Symptom**: `/admin` returns 404 after clean-URL middleware was added.
**Root cause**: middleware put `/admin` in `_NO_REWRITE_PREFIX` early-
return, which skipped the .html-rewrite step. Static-files mount couldn't
find a file called `admin` (only `admin.html`).
**Prevention**:
- The "no rewrite" set is for things that are TRULY internal (api/, q/,
  p/, sitemap, robots.txt) — NOT for HTML pages that just happen to start
  with that prefix.
- When in doubt, route requests through the rewrite step and only short-
  circuit on truly system-level prefixes.

---

## L7 — "Bbox containment fails for irregular emirate shapes"
**Symptom**: a point in Sharjah resolves to Dubai because Dubai's bbox
extends further north than Sharjah's centroid.
**Root cause**: rectangular bounding boxes overlap on emirate borders
(Dubai's bbox covers Sharjah city). First-match wins.
**Prevention**:
- For "which region is this point in" use NEAREST-CENTROID distance, not
  rectangular containment.
- Bbox is only a first-pass "is it inside the country at all" reject.
- Pattern: `app/address_picker.py::_which_emirate`.

---

## L8 — "Cookie not sent because secure=True on http://"
**Symptom**: TestClient auth flow works for /verify (sets cookie) but
subsequent /profile call returns "not authenticated".
**Root cause**: cookies marked `secure=True` are only sent over HTTPS.
TestClient uses `http://` so the browser-side equivalent (httpx) never
sends it back.
**Prevention**:
- Detect HTTPS via `request.url.scheme == "https" or
  request.headers.get("x-forwarded-proto","").startswith("https")`.
- Set `secure=is_https` so dev and production both work.
- Pattern: `app/customer_profile.py::auth_verify`.

---

## How to add a new lesson
When the user reports a bug or a test fails for a non-obvious reason:
1. Add a new `## Ln — <one-line title>` entry here
2. Mirror the prevention rule into `CLAUDE.md` under TESTING LOOPHOLES
3. Reference the entry in the commit message that fixes it
