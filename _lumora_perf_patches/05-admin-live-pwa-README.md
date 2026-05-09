# Admin Live PWA — apply guide

A standalone admin-only PWA at `/admin-live.html` that does Phase 1 + 2
combined: live visitor feed + live chat takeover + Web Push to phone +
auto-mirror to paired Wear OS / Apple Watch.

## What's added

### Backend (`app/admin_live.py` + 1 line in `app/main.py`)
6 new endpoints under `/api/admin/live/`:

| Endpoint | Purpose |
|---|---|
| `GET /active-chats` | last 30-min chat sessions |
| `GET /chat/{sid}` | full message history |
| `POST /chat/{sid}/reply` | admin reply (auto-takes over) |
| `POST /chat/{sid}/take` | manual takeover |
| `POST /chat/{sid}/release` | hand back to bot |
| `GET /feed?since=<iso>` | poll deltas since timestamp |

All require `Bearer ADMIN_TOKEN`.

### Frontend
| File | Purpose |
|---|---|
| `web/admin-live.html` | Single-file PWA — login + tabs + chat detail |
| `web/admin-live.js` | Polling, rendering, beep, push subscription |
| `web/admin-live-sw.js` | Service worker — receives Web Push, shows notif with Reply action, posts replies back |
| `web/admin-live.webmanifest` | PWA manifest — installable to home screen |

## How it works (the WhatsApp-style flow you asked for)

1. **Setup**: open `https://servia.ae/admin-live.html` in Chrome on phone → paste `ADMIN_TOKEN` once → tap **📲 Enable push**
2. **Add to home screen**: Chrome menu → "Add to home screen" → icon appears like a real app, no APK needed
3. **Pair your Wear OS watch** to the phone via Galaxy Wearable / Wear OS app (one-time, you've already done this)
4. **Wear OS auto-mirrors** every notification from the phone — including ours. With the **Reply** action button enabled, you get voice-or-text reply on the watch.
5. **New chat arrives** on the website → server fires Web Push → phone notification → watch mirror → tap Reply → speak/type → answer is posted to the customer's chat
6. **No watch APK needed.** The OS handles mirroring. Same channel WhatsApp uses.

## Apply (when in lumora-authorised Claude session)

```bash
cd <local lumora clone>
git apply 05-admin-live-pwa.patch
git add -A
git commit -m "feat: admin-live PWA with web push + watch mirroring"
git push origin main
```

Wait for Railway redeploy (~2 min). Then on phone:

1. Open `https://servia.ae/admin-live.html`
2. Paste your admin token
3. Tap **📲** to enable push
4. Tap Chrome menu → **Add to Home screen**

## Smoke test

Have a colleague (or another browser tab) chat with the bot at `https://servia.ae`. Within 4 sec the new session shows up in the **Chats** tab of admin-live, with sound. Tap the card → see the conversation → type a reply → it appears in the customer's chat as if from the bot.

## Limitations / known issues

- **First-tap on iOS Safari**: Web Push works but only in PWA mode (after Add to Home Screen). Chrome on Android works in any tab.
- **Token in service worker**: SW reply action retrieves token from any open PWA tab. If no PWA tab is open, tapping the notification just opens the PWA at the chat — admin types the reply manually. Works fine on watches that mirror the notification because the phone PWA is usually still in memory.
- **Polling, not WebSocket**: 4-sec polling is enough for ~99% of admin use cases and survives Railway sleep without reconnection logic. Switch to SSE later if you want sub-second latency.

## Roadmap after this

- Phase 1.5: visitor click-trail (every page they visit, not just the latest)
- Phase 2.5: bot tool-call hints in the chat detail (so admin sees what the bot was about to do)
- Phase 3: TWA wrapper (only if PWA's home-screen install isn't good enough)

## Why this is better than a separate Wear OS APK

You called this out perfectly: **WhatsApp doesn't need a watch app**. It works on the watch because:
1. WhatsApp on phone shows a notification
2. Wear OS / iOS notification mirroring auto-shows it on the watch
3. Notification has a "Reply" action that supports voice + canned replies

This admin PWA + Web Push uses **exactly the same OS-level mechanism**. No watch APK to maintain. No Galaxy Store / Play Store submission for a watch app. Just a phone PWA that the OS mirrors. Truly the right approach for your use case.
