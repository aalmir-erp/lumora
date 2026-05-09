# Servia Watch Face Pusher (Plan A)

Tiny watch APK that uses the **Watch Face Push API** to register
the bundled Burj Sunset face into the watch's pushed-faces registry.
This bypasses the `FLAG_SYSTEM` filter that hides sideloaded
watch faces from Samsung One UI Watch's picker UI.

## Install
1. Sideload `servia-wf-pusher-vNN.apk` from the CI artifact onto
   the watch (ADB / Bugjaeger / Easy Fire Tools).
2. Open **Servia Face Push** in the watch app drawer.
3. Tap **Push & Activate**.
4. First time only: grant `PUSH_WATCH_FACES` permission.
5. The face appears as the active watch face.

## What it does (under the hood)
1. Extracts the bundled `assets/burjsunset.apk` (the WFF v4 face
   payload — pure resource APK, ~80 KB) to internal cache.
2. Calls `WatchFacePushManager.addWatchFace(pfd, "")` with an empty
   validation token (works on developer-mode watches; production
   would need a Google-issued token).
3. Calls `setWatchFaceAsActive(slotId)` to flip the live face.

## If push fails
The `status` text in the activity shows the exact error. Common ones:

| Error | Fix |
|-------|-----|
| `WatchFacePushManager not available` | Watch is below Wear OS 5 / API 34 — no Push API. Plan F (Galaxy Store) is the only path. |
| `permission DENIED` | Settings → Apps → Servia Face Push → Permissions → enable "Push watch faces". |
| `Validation token rejected` | Watch isn't in developer mode, OR runtime requires real token. Enable Dev mode (Settings → About watch → Software info → tap Software version 7×). |

## Limits
- Watch Face Push has **slot limits** (typically 4 pushed faces per
  installer). Use the **Remove Pushed Face** button if you fill up.
- The face APK is signed with the same vendored CI keystore as the
  pusher — Push API requires both to share signing key.

## Roadmap
- [x] Single face, single button
- [ ] Bundle all 22 faces, picker UI inside the pusher
- [ ] Wearable Data Layer integration so the phone TWA can push by
      tapping a button on servia.ae
