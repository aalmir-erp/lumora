# Galaxy Store — Internal Testing Deploy (Plan C)

**Why this exists:** The Samsung One UI Watch picker on Galaxy Watch L310
(and likely all Galaxy Watches running Wear OS 6) filters watch faces by
the OS-set `FLAG_SYSTEM` flag. Sideloaded APKs never get this flag, so
they are silently filtered out of the picker UI even though they are
fully enumerated by `PackageManager.queryIntentServices`.

We confirmed this by direct ADB comparison:

| Package | flags |
|---------|-------|
| `com.samsung.android.watch.watchface.basicclock` (stock) | `[ SYSTEM HAS_CODE ALLOW_CLEAR_USER_DATA ]` |
| `ae.servia.wear.faces` (sideload) | `[ HAS_CODE ALLOW_CLEAR_USER_DATA ]` |

Galaxy Store-installed apps **do not** get the `SYSTEM` flag either, but
Galaxy Store has its own picker integration that bypasses the filter.
Distributing through Galaxy Store is therefore a viable production path
without re-engineering the entire face delivery pipeline.

---

## What you upload

The existing CI artifact `servia-android-twa` contains a Play-Console-
ready AAB **and** a sideload-ready APK. Galaxy Store accepts the same
AAB:

- File: `servia-twa-v1.24.NN-YYYYMMDD-HHMM.aab`
- Application ID: `ae.servia.app`
- Signing: Production keystore (vendored in `.ci/twa/keystore.jks.b64`)

Galaxy Store does **not** accept Play Store's special bundle format —
plain AAB is fine. If they reject it for any reason, fall back to the
APK from the same artifact bundle.

---

## Step-by-step

### 1. Sign up for Samsung Developers (free)
https://developer.samsung.com/galaxy → "Get started"

- Personal account is fine for internal testing.
- Need: legal name, Korean / international phone, email.
- Verification: 1–2 business days for payout details (not needed
  for internal testing distribution).

### 2. Open Seller Portal
https://seller.samsungapps.com/

This is the Galaxy Store equivalent of Google Play Console. Click
**"Add new application"**.

### 3. Choose "Wearable" as the application type
- Device class: **Galaxy Watch (Wear OS)**
- Region: **All countries** (or restrict to UAE if you want)
- Pricing: **Free**

### 4. Upload the AAB
- Drag the `servia-twa-vNN.aab` from the CI artifact zip
- Galaxy Store will reject if the app isn't a Wear app —
  for the **watch face** distribution use the wear AAB instead:
  `servia-wear-vNN.aab` from the `servia-android-wear` artifact.

For the **phone TWA**, use `servia-twa-vNN.aab`.

### 5. Fill in the metadata
Required:
- Title: `Servia` (or `Servia Watch Faces`)
- Short description: 80 chars max
- Full description: 4000 chars max
- Category: **Lifestyle** or **Productivity**
- Screenshots: at least 2 phone, 2 watch (use the previews from
  `web/brand/`)
- Privacy policy URL: `https://servia.ae/privacy.html`
- Content rating: All ages (UAE-friendly content)

### 6. Submit to Internal Testing Track
- In the upload flow, after metadata, choose **"Beta Test"**
  (Galaxy Store's term for internal testing — the production-test
  ladder is Beta → Open Beta → Production).
- Add up to 100 tester emails (just yours initially — `support@servia.ae`).
- Set rollout to **"Closed Beta"** so it doesn't appear in public
  search.
- Submit.

### 7. Review wait
- Internal testing apps typically pass review in **24–72 hours**
  (vs Play Store's 1–7 days).
- Email when approved.

### 8. Install on watch from Galaxy Store
- Open Galaxy Store on the watch (or on the phone's Galaxy Wearable
  app).
- Search for `Servia` → tap → install.
- Once installed, watch faces appear in **Settings → Customize watch
  faces** (or whatever Samsung calls it — picker UI integration is
  the whole point of Galaxy Store distribution).

---

## If Galaxy Store rejects the AAB

Most likely cause: **Samsung Knox Vault signature requirement**. If you
hit this, the workaround is:

1. Download the rejected AAB.
2. Re-sign with Samsung's required key bundle (Galaxy Store provides a
   tool: `galaxy-app-signer.jar`).
3. Re-upload.

The CI keystore at `.ci/twa/keystore.jks.b64` is a generic 2048-bit RSA
key. Galaxy Store accepts it. Knox is only enforced for finance / health
categories.

---

## Comparison to Play Store

|  | Play Store | Galaxy Store |
|---|---|---|
| Dev fee | $25 one-time | **Free** |
| Review time (internal) | ~5 min | 24–72 hr |
| Review time (production) | 1–7 days | 3–7 days |
| Watch face distribution | Native | Native |
| UAE coverage | ✅ | ✅ |
| Galaxy Watch picker integration | ✅ | ✅ |

For UAE-focused product like Servia, Galaxy Store is the better cost
choice. For broader market eventually, do both.

---

## Linked artifacts

- Phone TWA: `servia-android-twa` artifact, file `servia-twa-vNN.aab`
- Wear: `servia-android-wear` artifact, file `servia-wear-vNN.aab`
- Watch Face Pusher (Plan A): `servia-wf-pusher` artifact, file
  `servia-wf-pusher-vNN.apk` — separate sideload-only path that doesn't
  need any store at all (uses Watch Face Push API). See the README in
  the artifact zip.

---

_v1.24.54 — created when Plan D (install-source spoofing) failed at
the Android 16 cert layer and the SYSTEM-flag filter was identified as
the actual picker discriminator._
