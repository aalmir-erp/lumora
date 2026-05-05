# Servia iOS — Capacitor wrapper

iOS doesn't have a Trusted Web Activity equivalent. Apple has held the line
that PWAs run in Safari, full-stop. The two ways to ship `servia.ae` as an
App Store app are:

1. **PWA install (zero code)** — iOS 16.4+ supports "Add to Home Screen" with
   real PWA capabilities (push, share target, badge). This is already wired
   via `web/manifest.webmanifest` and works today. **No App Store listing**,
   but no submission, no fees, no review — users tap the share sheet.
   Documented in `web/install.html`.

2. **Native shell (this directory)** — wrap the site in a `WKWebView`
   Capacitor app. Required if you want a presence in the App Store.
   Capacitor is the modern successor to Cordova; same idea, much better
   tooling, used by Ionic.

We support both. Marketing pushes path 1 first (zero install friction); the
App Store listing exists for users who can't / won't sideload PWAs.

## Prerequisites (only on a Mac)

```bash
# Xcode 15+, command-line tools, CocoaPods
xcode-select --install
sudo gem install cocoapods

# Node + Capacitor CLI
npm install -g @capacitor/cli
```

## Initial scaffold

```bash
cd twa/ios
npx cap init "Servia" "ae.servia.app" --web-dir=public
# `public` is just a stub — Capacitor needs a directory to point at, but we
# override the launch URL to load servia.ae directly from the network.

# Add iOS platform
npm install @capacitor/ios @capacitor/core
npx cap add ios

# Open in Xcode
npx cap open ios
```

## Configure Xcode project

In `ios/App/App/Info.plist`, set:
- `CFBundleDisplayName` = `Servia`
- `CFBundleVersion` = `1.22.60`
- `CFBundleShortVersionString` = `1.22.60`
- `LSApplicationQueriesSchemes` = `["whatsapp", "tel", "mailto", "comgooglemaps", "comgooglemaps-x-callback"]`
- Privacy strings: `NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`, `NSContactsUsageDescription` (only if features need them)

In `capacitor.config.json`:

```json
{
  "appId": "ae.servia.app",
  "appName": "Servia",
  "webDir": "public",
  "server": {
    "url": "https://servia.ae",
    "androidScheme": "https",
    "iosScheme": "https",
    "cleartext": false,
    "allowNavigation": [
      "servia.ae",
      "*.servia.ae",
      "chatgpt.com",
      "wa.me",
      "*.stripe.com"
    ]
  },
  "ios": {
    "contentInset": "automatic",
    "scrollEnabled": true,
    "limitsNavigationsToAppBoundDomains": false
  },
  "plugins": {
    "PushNotifications": { "presentationOptions": ["badge", "sound", "alert"] },
    "SplashScreen": { "launchShowDuration": 600, "backgroundColor": "#0D9488" }
  }
}
```

## Splash + icons

Replace these in Xcode:
- `App/App/Assets.xcassets/AppIcon.appiconset/` — drop in
  `web/brand/servia-icon-1024x1024.png` (Xcode auto-generates the smaller
  sizes from this).
- `App/App/Assets.xcassets/Splash.imageset/` — use `web/brand/servia-icon-2048x2048.png`
  on a `#F8FAFC` background canvas (2732x2732 universal).

## Build + submit

```bash
# In Xcode:
# Product → Archive → Validate App → Distribute App → App Store Connect
# OR via command line:
xcodebuild -workspace ios/App/App.xcworkspace -scheme App archive -archivePath ./build/Servia.xcarchive
xcrun altool --upload-app -f ./build/Servia.ipa -u APPLE_ID -p APP_SPECIFIC_PASSWORD
```

Apple will reject if:
- The app is "just a website" with no app-shell features → workaround:
  enable push, share target, deep links, offline shell. Cite our PWA features
  in the App Review notes.
- Privacy policy URL missing → set to `https://servia.ae/privacy.html`
- Support URL missing → set to `https://servia.ae/contact.html`

Average review: 24–48 hours.

## Updating

- Web changes → instant, no review.
- Shell changes (splash, plugins, native code) → bump version in
  `Info.plist`, archive, re-submit.
