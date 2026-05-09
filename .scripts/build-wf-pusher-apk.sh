#!/usr/bin/env bash
# v1.24.54 — Build the Servia Watch Face Pusher APK.
#
# Depends on the wff-only APK already being built (its output is
# bundled into wf-pusher's assets/burjsunset.apk).
#
# Output: twa/android/wf-pusher-build/_artifacts/servia-wf-pusher-vNN-TS.apk

set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

SRC="twa/android/wf-pusher"
WFF_BUILD="twa/android/wff-only-build/_artifacts"
BUILD_DIR="twa/android/wf-pusher-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

if [ ! -f "$WFF_BUILD/burjsunset.apk" ]; then
  echo "::error::Face payload missing at $WFF_BUILD/burjsunset.apk."
  echo "::error::Run .scripts/build-wff-only-apk.sh first."
  exit 1
fi

echo "=== Setting up Servia Watch Face Pusher gradle project at $BUILD_DIR ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/wfpusher"
mkdir -p "$BUILD_DIR/app/src/main/res/values"
mkdir -p "$BUILD_DIR/app/src/main/res/layout"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-hdpi"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-xhdpi"
mkdir -p "$BUILD_DIR/app/src/main/assets"

# ---- Manifest + Java + resources ----
cp -v "$SRC/AndroidManifest.xml"           "$BUILD_DIR/app/src/main/AndroidManifest.xml"
cp -v "$SRC/java/ae/servia/wfpusher/PushActivity.java" "$BUILD_DIR/app/src/main/java/ae/servia/wfpusher/"
cp -v "$SRC/res/values/strings.xml"        "$BUILD_DIR/app/src/main/res/values/"
cp -v "$SRC/res/layout/activity_push.xml"  "$BUILD_DIR/app/src/main/res/layout/"

# ---- Bundle the face payload ----
cp -v "$WFF_BUILD/burjsunset.apk" "$BUILD_DIR/app/src/main/assets/burjsunset.apk"
echo "Payload size: $(stat -c%s "$BUILD_DIR/app/src/main/assets/burjsunset.apk" 2>/dev/null || stat -f%z "$BUILD_DIR/app/src/main/assets/burjsunset.apk") bytes"

# ---- Launcher icon (reuse Servia's) ----
ICON_SRC="web/brand/servia-icon-512x512.png"
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-hdpi/ic_launcher.png"
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-xhdpi/ic_launcher.png"
fi

# ---- build.gradle ----
cp -v "$SRC/build.gradle" "$BUILD_DIR/app/build.gradle"
APP_VER=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
if [ -n "$APP_VER" ]; then
  sed -i -E "s/versionName \"[^\"]*\"/versionName \"$APP_VER\"/" "$BUILD_DIR/app/build.gradle"
fi

# ---- Top-level ----
cat > "$BUILD_DIR/build.gradle" <<'GRADLE'
buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.5.2' }
}
allprojects { repositories { google(); mavenCentral() } }
GRADLE
cat > "$BUILD_DIR/settings.gradle" <<'GRADLE'
rootProject.name = "servia-wf-pusher"
include ':app'
GRADLE

GW_DIR="twa/android/generated"
mkdir -p "$BUILD_DIR/gradle/wrapper"
cp -r "$GW_DIR/gradle/wrapper/." "$BUILD_DIR/gradle/wrapper/"
cp "$GW_DIR/gradlew" "$BUILD_DIR/gradlew"
cp "$GW_DIR/gradlew.bat" "$BUILD_DIR/gradlew.bat" 2>/dev/null || true
chmod +x "$BUILD_DIR/gradlew"

cat > "$BUILD_DIR/gradle.properties" <<'PROPS'
android.useAndroidX=true
android.enableJetifier=false
org.gradle.jvmargs=-Xmx2048m
android.suppressUnsupportedCompileSdk=34
PROPS

# ---- Build ----
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/pusher-gradle.log
set +e; set +o pipefail
./gradlew --no-daemon --stacktrace --info \
    -Pandroid.injected.signing.store.file="$KS_PATH" \
    -Pandroid.injected.signing.store.password="${KEYSTORE_PASS:-placeholder}" \
    -Pandroid.injected.signing.key.alias="${KEY_ALIAS:-servia}" \
    -Pandroid.injected.signing.key.password="${KEY_PASS:-placeholder}" \
    bundleRelease assembleRelease 2>&1 | tee "$LOG" | tail -120
GRADLE_EXIT=${PIPESTATUS[0]}
set -e; set -o pipefail
tail -300 "$LOG" > _artifacts/pusher-gradle-tail.txt 2>/dev/null || true

APP_VERSION=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
BUILD_TS=$(date -u +%Y%m%d-%H%M)
SUFFIX="v${APP_VERSION}-${BUILD_TS}"
find app/build/outputs -name "*.apk" -exec cp {} "_artifacts/servia-wf-pusher-${SUFFIX}.apk" \; 2>&1 || true
find app/build/outputs -name "*.aab" -exec cp {} "_artifacts/servia-wf-pusher-${SUFFIX}.aab" \; 2>&1 || true
echo "$SUFFIX" > _artifacts/PUSHER_BUILD_INFO.txt
ls -la _artifacts/

if [ "$GRADLE_EXIT" != "0" ]; then exit "$GRADLE_EXIT"; fi
if [ -z "$(ls _artifacts/servia-wf-pusher-${SUFFIX}.apk 2>/dev/null)" ]; then
  echo "::error::Pusher produced 0 APK"
  exit 1
fi
