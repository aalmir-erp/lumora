# Lumora Performance Patches

Applied to a clone of `aalmir-erp/lumora` at `/tmp/lumora-deploy/`. Couldn't
push directly because this Claude session's signing token doesn't include
lumora in its `sources` allowlist. Use these patches via a new lumora session.

## What's in `01-defer-health-and-logo-dims.patch`

33 files modified, 42 insertions, 35 deletions. Two changes:

### A. `web/app.js` — defer `/api/health` fetch off the critical path
The `_setVersion()` function used to fire on `DOMContentLoaded` which made
PageSpeed Insights see `/api/health` (~7,400ms on mobile) as a critical-path
request blocking LCP. Now wrapped in `requestIdleCallback` (or `load + 1500ms`
fallback). **Expected impact**: LCP element render delay drops from 5,970ms
to <500ms. Performance score +15–20 points on mobile.

### B. All HTML files — add explicit `width="112"` to footer logo
Every footer `<img src="/logo.svg" height="36" ...>` was missing `width`,
triggering CLS warnings on PageSpeed. Now `width="112" height="36"`.
**Expected impact**: CLS stays at 0, eliminates the "Image elements do not
have explicit width and height" diagnostic. Performance +1–2.

## How to apply

In a Claude Code session pointed at `aalmir-erp/lumora`:

```
cd <local lumora clone>
git apply <path-to>/01-defer-health-and-logo-dims.patch
git add -A
git commit -m "perf: defer /api/health, add explicit width to footer logo"
git push origin main
```

Wait for the Railway deploy → re-run PageSpeed → expect mobile to jump from
~61 to ~80+.

## Bigger wins NOT in this patch (need separate work)

| Issue | Estimated points | Where to fix |
|---|---|---|
| Cloudflare Email Obfuscation injecting 3.8s of `email-decode.min.js` | +10 mobile | CF dashboard (no code) — Scrape Shield → Email Address Obfuscation → OFF |
| Railway free-tier cold starts on `/api/health` | +5–10 | Set up an external pinger every 5 min (Cloudflare Workers cron, UptimeRobot, etc.) OR upgrade Railway plan |
| Style & Layout 6.85s | +5–10 | Audit CSS — too many properties on `body` are recomputing. Move animations to `transform`/`opacity` only |
| 14 long main-thread tasks | +5 | Profile with Chrome DevTools Performance panel; chunk JS work with `requestIdleCallback` or break up large loops |
| 29 non-composited animations | +3 | Convert keyframe `transform: scale()` etc. to use `will-change: transform` |
| `app.js` + `widget.js` unminified | +1 | Add a build step to minify (terser/esbuild). Currently served raw. |

## Realistic Lighthouse target

**Mobile 100 is rare** for any production site with >100KB of JS. Most well-optimised commerce sites land in the 85–95 range on mobile. Desktop 95–100 is achievable. The patch in this folder + the CF email-obfuscation toggle should get mobile from 61 → 80+ and desktop from 73 → 90+.

For 100/100 a separate refactor pass is needed: server-side rendering or static export of the marketing pages, aggressive code-splitting, switching from JS-driven layout to CSS-only, etc.

---

**Created**: v1.24.54 session, while signing infra blocked direct lumora pushes.
