# Servia Watch Face — Galaxy Store + Watch Face Push API

> v1.24.54 — strategy doc. Background, rationale, and the two parallel
> distribution paths we are pursuing.

## What we proved in v1.24.45 → v1.24.52

Sideloading watch faces onto a Galaxy Watch (One UI Watch) is a dead
end for third-party apps:

| Build      | Approach                                                   | Result                                                                |
| ---------- | ---------------------------------------------------------- | --------------------------------------------------------------------- |
| v1.24.45   | 22 services, AndroidX Watch Face Format APK                | Installs, but no faces in picker.                                     |
| v1.24.49   | Smart-rebuild infra so iteration is cheap                  | Infra OK.                                                             |
| v1.24.50   | Inject `APP_VERSION` + add diagnostic endpoint             | Confirmed APK on watch matches CI build.                              |
| v1.24.51   | Multi-attempt Apply intents + Samsung-specific intents     | Apply button toasts succeed but face never activates.                 |
| v1.24.52   | Plan B: legacy `WallpaperService` face matching Samsung's `DefaultWatchFace` shape exactly | Same outcome — face is invisible to Samsung's One UI Watch picker. |

**Root cause:** Samsung's One UI Watch picker enumerates watch face
services using `PackageManager.getServicesByMetaData()` and then
filters the result by `ApplicationInfo.flags & FLAG_SYSTEM != 0`.
Sideloaded APKs do not have `FLAG_SYSTEM`. Galaxy Store-installed
apps do (or are equivalent for picker-eligibility purposes). Google
Play-installed Wear OS apps also pass the gate on Pixel/AOSP-derived
watches but **do not** pass it on Samsung One UI Watch.

We have no path to flip `FLAG_SYSTEM` on a sideloaded APK. So:

## Two parallel distribution paths from v1.24.54

### Path A — Watch Face Push API (PRIMARY, ships in this build)

Google added the Watch Face Push API in January 2025
(`androidx.wear.watchface:watchface-push:1.0.0-alpha+`). It lets a
companion Wear OS app install a Watch Face Format APK on the same
watch via a system service, **bypassing the picker enumeration that
Samsung filters**. The face appears in the user's customisable face
list because the system itself put it there, not because the picker
walked the package list.

Available on Wear OS 5.1+ — which is exactly the One UI 5+ devices
where sideloading is currently broken. The Push API is the only known
path to put a third-party face on a Galaxy Watch without going through
Galaxy Store.

#### Components (all in this commit)

```
twa/android/wff-only/         pure WFF payload (no Java, no service)
twa/android/wf-pusher/        Wear OS app that calls WatchFacePushManager
.scripts/build-wff-only-apk.sh
.scripts/build-wf-pusher-apk.sh
```

#### Test workflow on a Galaxy Watch via Bugjaeger

1. Pair watch over Wi-Fi-ADB (Bugjaeger handles the handshake).
2. `adb install` BOTH `servia-wff-burj-sunset-vXX.apk` AND
   `servia-wf-pusher-vXX.apk`. Order matters: the WFF payload APK
   must be present (or, alternately, bundled inside the pusher's
   `res/raw/payload.apk` — which build-wf-pusher-apk.sh does
   automatically).
3. Open "Servia Pusher" on the watch.
4. Tap **PUSH**.
5. Expected: log shows `addWatchFace() returned: ...`, then
   `Slot: Slot{slotId=...}`, then `PUSH OK`. Face becomes selectable
   from the system "Customize watch faces" list.
6. If the face does not auto-activate, the same activity also
   attempts `setWatchFaceAsActive(slotId)` — check the log for
   "Set active OK".

#### Failure-mode debugging

The Push API is alpha. Expect rough edges:

- `PERMISSION_DENIED` → confirm `com.google.wear.permission.PUSH_WATCH_FACES` is granted. On Wear OS 5.1+ it's auto-granted at install but Samsung occasionally requires an explicit user grant.
- `INVALID_PAYLOAD` → the WFF payload APK isn't a valid WFF document. Validate by side-installing it on the watch and confirming the system at least *recognises* it as a watch-face package (it won't appear in the picker, but `pm dump` should show the WFF metadata).
- `SIGNATURE_MISMATCH` → the wff-only and wf-pusher APKs were signed with different certs. Both should be CI-built in the same job so the keystore is shared.
- The Push API class is missing entirely → device is on Wear OS < 5.1, or the OEM hasn't shipped the implementation yet. Falls through to Path B.

### Path B — Galaxy Store (BACKUP, design only in this commit)

Galaxy Store-installed apps qualify for `FLAG_SYSTEM` on Samsung
watches even without explicit OEM partnership. Cost: $0 dev-account
fee for individuals. Review: 1–7 days.

#### Submission requirements

1. **Galaxy Watch Studio account** — separate from the Galaxy Store
   seller console. Free.
2. **Standalone Wear OS APK** — signed AAB with `<uses-feature android:name="android.hardware.type.watch" />`.
3. **A Watch Face APK** — the existing `wear-faceonly/` build in this
   repo, signed with our prod cert. (Single Burj Sunset face, not all
   22, to keep the review surface small for the first submission.)
4. **Privacy URL** — point to https://servia.ae/privacy.html.
5. **Listing assets** — three 480×480 round previews of the face on a
   Watch7 mockup; we already render these from `wf_frame_p01.png`.

#### Why we are not doing Path B yet

- Galaxy Store reviewers disallow apps that are "purely a watch face
  + nothing else." Servia Wear has utility (tiles, complications), so
  we likely qualify, but the first submission will need to bundle the
  pusher APK with the rest of the wear app, not as a standalone.
- The Push API path is a single cert + two APKs and we can iterate
  hourly via `adb install`. Galaxy Store iteration is daily at best.

We will fall back to Path B if the Push API still doesn't surface the
face after one hardware test cycle.

## Build cadence

`workflow_dispatch` with `target=wff` builds just the WFF payload.
`target=pusher` builds the pusher (and re-builds the payload first —
the pusher embeds it). `target=auto` (default for pushes) detects
which subtree changed.

```
- name: Build Servia WFF-only payload
  run: .scripts/build-wff-only-apk.sh "$RUNNER_TEMP/servia.jks"

- name: Build Servia Watch Face Pusher
  run: .scripts/build-wf-pusher-apk.sh "$RUNNER_TEMP/servia.jks"
```

Artifacts emitted:

- `servia-wff-burj-sunset-vXX-TIMESTAMP.apk` (~120–180 KB)
- `servia-wf-pusher-vXX-TIMESTAMP.apk`        (~3–4 MB; pulls in
  androidx.wear.watchface:watchface-push)

Both available from Actions → run → Artifacts → `servia-wf-pusher`
(the pusher artifact bundle includes the wff-only APK alongside).
