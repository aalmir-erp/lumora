# Servia Mobile Apps

This directory contains the build configs for shipping `servia.ae` as
native-feeling apps to the Play Store (Android) and the App Store (iOS).

| Platform | Tech         | What it is                                                   | Where  |
|----------|--------------|--------------------------------------------------------------|--------|
| Android  | TWA          | Trusted Web Activity via Bubblewrap. Full-screen, no chrome. | `android/` |
| iOS      | Capacitor    | WKWebView shell pointed at servia.ae.                        | `ios/`     |
| Web/PWA  | manifest.webmanifest | Add-to-Home-Screen on iOS 16.4+ and any Chromium browser. | `../web/manifest.webmanifest` |

## Recommended order of attack

1. **PWA first** — already live. Zero engineering cost. `/install.html`
   walks the user through installing.
2. **Android TWA** — single-day build, Play Store in ~3 days. Highest ROI
   because the UAE is a heavily-Android market.
3. **iOS Capacitor** — only if you want App Store presence. App Review takes
   24–48h once the build is ready, but native-shell setup takes a day.

Each subdir has a self-contained README with step-by-step build commands.

## Asset Links / Universal Links

The TWA needs `https://servia.ae/.well-known/assetlinks.json` (already
committed at `web/.well-known/assetlinks.json`) with the SHA-256 fingerprint
of the signed APK. Update that fingerprint placeholder after the first
Bubblewrap build.

Capacitor doesn't strictly need a `.well-known/apple-app-site-association`
unless we want Universal Links (deep-linking from emails / SMS into specific
app screens). Skip until the App Store build is approved.
