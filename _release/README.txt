⚠️  CONFIDENTIAL — DO NOT MAKE THIS REPO PUBLIC ⚠️

This `_release/` folder contains the Android upload keystore for
`ae.servia.app` plus its decryption password. If this folder ever
leaks to a public location, malicious actors could publish updates
to the Servia app on Google Play under your developer account.

═══════════════════════════════════════════════════════════════════
FILES
═══════════════════════════════════════════════════════════════════

  upload-keystore.b64          base64-encoded keystore (binary jks)
                                Used by .github/workflows/play-verification-build.yml
                                to sign verification APKs.

  upload-keystore.jks          raw keystore (gitignored — only in sandbox + your
                                backups). Do NOT commit this file.

  keystore-password.txt        password for the keystore + the key inside.
                                Auto-generated 32-char strong random string.

  keystore-sha256.txt          SHA-256 public fingerprint. Paste this into
                                Play Console "Change key" / "Eligible public key"
                                section of the Android Developer Verification page.

  verification-snippet.txt     (created later) the snippet from Play Console
                                ("C0B2JHE7AEDB0AAAAAA..." string). When
                                committed, triggers workflow 02 to build the APK.

═══════════════════════════════════════════════════════════════════
SHA-256 FINGERPRINT TO PASTE INTO PLAY CONSOLE
═══════════════════════════════════════════════════════════════════

See keystore-sha256.txt — copy that exact string into Play Console.

═══════════════════════════════════════════════════════════════════
FUTURE RELEASES OF THE ACTUAL SERVIA APP
═══════════════════════════════════════════════════════════════════

When building the real Servia app (TWA + Wear OS) for release to
Play Store, sign with the same keystore using:

  keystore: _release/upload-keystore.jks  (or base64-decode .b64)
  alias:    servia-upload
  password: contents of _release/keystore-password.txt

Same keystore for every future update — Play Store requires this.
If you ever switch to Play App Signing (recommended), the upload
key in Play Console MUST remain this same one.

═══════════════════════════════════════════════════════════════════
KEYSTORE ROTATION
═══════════════════════════════════════════════════════════════════

If this keystore is compromised, you can request "Reset upload key"
from Play Console (Settings → App integrity → App signing). Google
needs ~48 hours to verify your identity and reset. Once reset, you
generate a fresh keystore and update Play Console. Do this if:
  - This repo accidentally goes public
  - Anyone outside your trust circle gets access
  - You suspect anyone has copied the keystore

═══════════════════════════════════════════════════════════════════
LICENSE
═══════════════════════════════════════════════════════════════════

These keystore files are not licensed for use by anyone except the
Servia FZ-LLC team. Possession by any other party is unauthorized.
