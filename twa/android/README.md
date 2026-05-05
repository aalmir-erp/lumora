# Servia Android — Trusted Web Activity (TWA)

Wraps `https://servia.ae` in a native Android shell so it can ship to the Play
Store and look identical to a fully-native app. Uses the official Bubblewrap
CLI from the Chrome team. The TWA shows the live website with no browser chrome
— users won't be able to tell it's not a "real" Android app.

## Why TWA, not React Native or Flutter

- Zero duplicate codebase. The website is the app — same HTML, same CSS, same
  JS. A bug fix on the website is also a bug fix in the app.
- Push notifications work via standard web push (already wired into the PWA).
- Play Store eligible — Google explicitly supports TWAs as a first-class app
  format since 2019.
- Smaller APK (~3 MB instead of 30+ MB for React Native).

## One-time prerequisites

```bash
# 1. Java 17 + Android SDK (only required to *build* — not for users)
sudo apt-get install -y openjdk-17-jdk
# Android cmdline-tools: download from
# https://developer.android.com/studio#command-tools

# 2. Bubblewrap CLI
npm install -g @bubblewrap/cli

# 3. Verify
bubblewrap doctor
```

## Building the APK / AAB

From the repo root:

```bash
cd twa/android
bubblewrap init --manifest=twa-manifest.json
# Bubblewrap reads the manifest, generates the Android Studio project.
# When asked, accept defaults — manifest already has the right values.

bubblewrap build
# Produces:
#   app-release-signed.apk        (test on a phone)
#   app-release-bundle.aab         (upload to Play Console)
```

The first build prompts to create a signing key. **Save the keystore + password
in 1Password / a vault** — losing it means you can never update the app on the
Play Store.

## Installing on a phone for testing

```bash
adb install app-release-signed.apk
# OR upload to Firebase App Distribution / Play Internal Testing
```

## Digital Asset Links — REQUIRED

For the TWA to launch without a URL bar (full-screen native feel), Android
needs cryptographic proof that you own both the app **and** the website. After
your first signed build, Bubblewrap prints a SHA-256 fingerprint. Drop it into:

```
web/.well-known/assetlinks.json   → served at https://servia.ae/.well-known/assetlinks.json
```

A starter file is committed at that path with a placeholder. Replace
`SHA256_FINGERPRINT_HERE` with the value Bubblewrap prints.

## Play Store submission checklist

1. Build AAB (`bubblewrap build`)
2. Play Console → Create app → upload AAB
3. App content questionnaire (data safety: we collect name, email, phone, address — declare it honestly)
4. Screenshots: 5+ phone, 2+ tablet (1080x1920 minimum). Use real screenshots from servia.ae.
5. Listing copy: pull from `/install.html` page
6. Pricing: Free
7. Countries: All — primary market AE
8. Internal testing → closed testing → production

Average Play review: 1–7 days. We're a service-area business, expect zero
issues since we're a real registered UAE company.

## Updating the app

Two paths:
1. **Website-only changes** — happen instantly. Users see the new content
   on next app open. No Play Store review needed.
2. **App-shell changes** (icon, splash, deep links) — bump `appVersionCode` in
   `twa-manifest.json`, rebuild, re-upload AAB.
