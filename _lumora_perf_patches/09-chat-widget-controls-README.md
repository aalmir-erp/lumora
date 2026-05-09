# Patch 09 — Chat widget controls + persistent state

Fixes 5 things you reported:

| Issue | Fix |
|---|---|
| No way to **minimize** the widget | Added "—" button in header — collapses to header strip; click again to expand |
| No way to **maximize / resize** | Added "⛶" button — toggles full-screen mode |
| No way to **download chat transcript** | Added "⤓" button — downloads `servia-chat-{sessionId}.txt` with timestamps + full conversation |
| No way to **start new chat** | Added "✨" button — clears localStorage, resets session, fresh greet |
| Chat **NOT persisted across page change/refresh** | Switched from sessionStorage to localStorage for open-state, size-state. Existing `restoreHistory()` already pulled past messages from server but the open state was wiped on tab close — now persists. |

## What changed

| File | What |
|---|---|
| `web/widget.js` | New header buttons + handlers, switched persistence to localStorage |
| `web/widget.css` | Styles for new buttons, `.us-min-state` + `.us-max-state` size classes |

## Behaviour after applying

### Persistence
- Customer opens chat, sends 3 messages, closes browser
- Customer comes back tomorrow → opens any servia.ae page → widget auto-opens (if it was open) AND shows ALL previous messages from today's session
- Persists across:
  - Page navigation (within same session)
  - Browser refresh (F5)
  - Browser close + reopen (next day, next week)
  - Until customer taps **✨ New chat** button

### Minimize button (—)
- Tap once → collapses to just the header strip (54px tall)
- Tap again → restores to normal size
- State saved across page loads

### Resize button (⛶)
- Tap once → fills entire viewport
- Tap again → restores to normal floating size
- On mobile (<600px) full screen is edge-to-edge

### Download (⤓)
Generates a text file like:
```
Servia chat transcript
Session: 0192abc-def-456
Downloaded: 2026-05-09T10:32:00Z

================================================

[2026-05-09 10:15:01] You:
How much for deep clean 1BR?

[2026-05-09 10:15:08] Servia:
Great question — for a 1-bedroom deep clean...
```

### New chat (✨)
- Confirms: "Start a new chat?"
- Wipes session_id from localStorage
- Body clears, fresh greeting plays
- Old session is NOT deleted from server — admin can still see it

## Apply

```bash
git apply _lumora_perf_patches/09-chat-widget-controls.patch
git add -A && git commit -m "feat(widget): min/max/download/new-chat + persist across refresh"
git push origin main
```

After Railway redeploys (~30 sec — only static files changed):
1. Hard-refresh servia.ae (Ctrl+Shift+R or pull-to-refresh on phone)
2. Open chat → see new buttons in the green header
3. Send a message → refresh page → chat history is still there

## Total lines
132 lines

## Cumulative
9 patches, ~5,700 insertions.
