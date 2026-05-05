# How to install Servia as an app — three paths

Honest summary of what's actually built right now (Nov 2026):

| Path                             | Status            | Effort to ship | Cost          | Where users get it          |
|----------------------------------|-------------------|----------------|---------------|-----------------------------|
| **PWA install** (Add to Home)    | ✅ live today     | zero           | $0            | Any browser, any phone      |
| **Android TWA → Play Store**     | 🟡 config in repo, AAB not built yet | 1 keystore + 1 GitHub secret + 1 click | $25 once  | Play Store search "Servia"  |
| **iOS Capacitor → App Store**    | ⚠️ requires Mac with Xcode | 1 day | $99 / year | App Store search "Servia"   |

There is **no APK or IPA in the repo yet.** Below is exactly how to ship each one.

---

## 1. PWA install — works right now, zero effort

Already wired into `web/manifest.webmanifest`. Tell users:

- **Android Chrome / Edge**: visit https://servia.ae → tap the address bar → "Install app". Or visit `/install.html` for a guided walkthrough.
- **iPhone Safari (iOS 16.4+)**: visit https://servia.ae → tap Share → "Add to Home Screen".
- **Desktop Chrome / Edge**: visit servia.ae → click the install icon in the address bar.

The PWA gets its own icon, splash screen, push notifications, and offline shell. **No store listing required** — but it's also not in any store, so users have to know to install it.

---

## 2. Android Play Store via TWA — quickest path to an actual store listing

The infrastructure is in place:

- `twa/android/twa-manifest.json` — Bubblewrap manifest (package `ae.servia.app`, all icons, shortcuts, splash colors)
- `web/.well-known/assetlinks.json` — Digital Asset Links file (placeholder fingerprint)
- `app/main.py` — already serves the assetlinks file at `https://servia.ae/.well-known/assetlinks.json`
- `.github/workflows/build-android-twa.yml` — **GitHub Actions workflow that builds the signed AAB for you** (so you don't need a local Android SDK)

### Step-by-step

**A. Generate a keystore (once, locally — keep it forever):**

```bash
keytool -genkeypair -v -keystore servia.jks -keyalg RSA -keysize 2048 \
        -validity 10000 -alias servia
# It'll prompt for a keystore password and a key password — use a strong one.
# SAVE BOTH PASSWORDS IN 1PASSWORD. Losing them means you can never update the app.
base64 servia.jks > servia.jks.b64    # encode for GitHub secret
```

**B. Add 4 GitHub Actions secrets** (Repo → Settings → Secrets and variables → Actions):

| Secret name                  | Value                                          |
|------------------------------|------------------------------------------------|
| `ANDROID_KEYSTORE_BASE64`    | full contents of `servia.jks.b64`              |
| `ANDROID_KEY_ALIAS`          | `servia`                                       |
| `ANDROID_KEYSTORE_PASSWORD`  | the keystore password from step A              |
| `ANDROID_KEY_PASSWORD`       | the key password from step A (often the same) |

**C. Trigger the build:**

GitHub → Actions tab → "Build Android TWA (AAB for Play Store)" → "Run workflow" → main → Run.

Takes ~5 minutes. When it finishes, download the artifact `servia-android-twa.zip`. It contains:

- `app-release-bundle.aab` — upload this to the Play Console
- `app-release-signed.apk` — install on a phone for testing (`adb install`)
- `assetlinks.json` — contains the SHA-256 fingerprint of YOUR signed APK

**D. Copy the SHA-256 from the generated `assetlinks.json` into `web/.well-known/assetlinks.json`** in the repo (replace the `REPLACE_WITH_SHA256_FROM_BUBBLEWRAP_BUILD_OUTPUT` placeholder), commit, push. Without this step the app opens with a Chrome URL bar instead of going full-screen.

**E. Submit to Play Console** (https://play.google.com/console — $25 one-time fee):

1. Create app → name "Servia" → package `ae.servia.app`
2. Upload `app-release-bundle.aab`
3. Fill out:
   - **Privacy policy URL**: https://servia.ae/privacy.html ✓ (already exists)
   - **Support URL**: https://servia.ae/contact.html ✓
   - **Data safety**: declare we collect name, email, phone, address (we do)
   - **Screenshots**: 5+ phone screenshots from servia.ae (1080×1920+)
   - **Short description** (80 chars): "UAE home services in 60 seconds. Cleaning, AC, handyman, all 7 emirates."
   - **Full description**: pull from `/install.html`
   - **Categories**: Lifestyle (primary), Shopping
   - **Country**: All countries (primary market UAE)
4. Submit for review. Average wait: **1–7 days**.

**F. Updating the app later:**

- **Website-only changes** (UI, content, prices) → instant. Users see new version on next open. No Play resubmission.
- **Shell changes** (icon, splash, deep-link rules) → bump `appVersionCode` in `twa/android/twa-manifest.json`, run the GitHub Actions workflow again, upload the new AAB to Play Console as a new release.

---

## 3. iOS App Store — requires a Mac

**Honest version**: there is no Trusted Web Activity equivalent on iOS. Apple won't allow it. The only path to App Store presence is wrapping the site in a `WKWebView` Capacitor app.

### What you need:

- A **Mac running macOS 14+** with Xcode 15+ (~25 GB disk)
- An **Apple Developer account** ($99 / year, https://developer.apple.com/programs/)
- Roughly a day of one-time setup, then ~30 min per release

### Prep work I can do in this repo:

I scaffolded `twa/ios/README.md` with the Capacitor commands. I can also generate a starter `capacitor.config.json` if you want — say the word.

### Prep work that requires the Mac:

```bash
# Install once
xcode-select --install
sudo gem install cocoapods
npm install -g @capacitor/cli

# In the repo
cd twa/ios
npx cap init "Servia" "ae.servia.app" --web-dir=public
mkdir public && touch public/index.html   # placeholder; real content is fetched from servia.ae
npm install @capacitor/ios @capacitor/core
npx cap add ios

# Configure the WKWebView to load servia.ae directly:
# edit capacitor.config.json — see twa/ios/README.md for the snippet

# Build + sign + upload
npx cap open ios
# In Xcode: Product → Archive → Validate App → Distribute App → App Store Connect
```

App Review average: **24–48 hours**.

Apple sometimes rejects apps that are "just a website". Mitigations:
- Enable web push (already in our manifest)
- Use the share target (already wired)
- Cite the offline shell + native-feeling UX in the App Review notes

### Cheaper alternative (no Mac, no $99):

Skip the App Store. iOS 16.4+ supports proper PWA install via Safari's "Add to Home Screen" with push notifications, badges, and share targets. **Most users won't notice the difference.**

---

## TL;DR — what to do right now

1. **Today**: Promote the PWA path on `/install.html` and in marketing. Zero work.
2. **This week**: Generate the Android keystore (5 min), add 4 GitHub secrets (5 min), run the GitHub Actions workflow once (5 min wait), download the AAB, submit to Play Console ($25, 1–7 day review).
3. **When you have access to a Mac**: do the Capacitor setup. Until then, the iOS PWA install path covers ~95% of what an App Store listing would.
