#!/usr/bin/env bash
# v1.24.54 — Build the Servia WFF face payload APK (Burj Sunset).
#
# This APK is the PAYLOAD of the wf-pusher app. It contains pure WFF
# resources (no Java) and is consumed by WatchFacePushManager.addWatchFace
# on the watch. Output is copied into wf-pusher's assets/ at the next
# build stage.
#
# Output: twa/android/wff-only-build/_artifacts/servia-wff-vNN-TS.apk

set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

SRC="twa/android/wff-only"
WEAR_SRC="twa/android/wear"
BUILD_DIR="twa/android/wff-only-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

echo "=== Setting up Servia WFF face gradle project at $BUILD_DIR ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app/src/main/res/values"
mkdir -p "$BUILD_DIR/app/src/main/res/raw"
mkdir -p "$BUILD_DIR/app/src/main/res/drawable"

# ---- Manifest + resources ----
cp -v "$SRC/AndroidManifest.xml"     "$BUILD_DIR/app/src/main/AndroidManifest.xml"
cp -v "$SRC/res/values/strings.xml"  "$BUILD_DIR/app/src/main/res/values/"
cp -v "$SRC/res/raw/watchface.xml"   "$BUILD_DIR/app/src/main/res/raw/"

# ---- Drawables ----
cp -v "$WEAR_SRC/res-drawable/wf_frame_p01.png"   "$BUILD_DIR/app/src/main/res/drawable/frame.png"
if [ -f "$WEAR_SRC/res-drawable/wf_preview_p01.png" ]; then
  cp -v "$WEAR_SRC/res-drawable/wf_preview_p01.png" "$BUILD_DIR/app/src/main/res/drawable/preview.png"
else
  cp -v "$BUILD_DIR/app/src/main/res/drawable/frame.png" "$BUILD_DIR/app/src/main/res/drawable/preview.png"
fi

# ---- build.gradle ----
cp -v "$SRC/build.gradle" "$BUILD_DIR/app/build.gradle"
APP_VER=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
if [ -n "$APP_VER" ]; then
  sed -i -E "s/versionName \"[^\"]*\"/versionName \"$APP_VER\"/" "$BUILD_DIR/app/build.gradle"
fi

# ---- Top-level project files ----
cat > "$BUILD_DIR/build.gradle" <<'GRADLE'
buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.5.2' }
}
allprojects { repositories { google(); mavenCentral() } }
GRADLE
cat > "$BUILD_DIR/settings.gradle" <<'GRADLE'
rootProject.name = "servia-wff-face"
include ':app'
GRADLE

# Reuse gradle wrapper
GW_DIR="twa/android/generated"
if [ -d "$GW_DIR/gradle/wrapper" ]; then
  mkdir -p "$BUILD_DIR/gradle/wrapper"
  cp -r "$GW_DIR/gradle/wrapper/." "$BUILD_DIR/gradle/wrapper/"
  cp "$GW_DIR/gradlew" "$BUILD_DIR/gradlew"
  cp "$GW_DIR/gradlew.bat" "$BUILD_DIR/gradlew.bat" 2>/dev/null || true
  chmod +x "$BUILD_DIR/gradlew"
else
  echo "::error::no gradle wrapper to borrow"
  exit 1
fi

cat > "$BUILD_DIR/gradle.properties" <<'PROPS'
android.useAndroidX=true
android.enableJetifier=false
org.gradle.jvmargs=-Xmx2048m
android.suppressUnsupportedCompileSdk=34
PROPS

# ---- Build ----
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/wff-gradle.log
set +e; set +o pipefail
./gradlew --no-daemon --stacktrace --info \
    -Pandroid.injected.signing.store.file="$KS_PATH" \
    -Pandroid.injected.signing.store.password="${KEYSTORE_PASS:-placeholder}" \
    -Pandroid.injected.signing.key.alias="${KEY_ALIAS:-servia}" \
    -Pandroid.injected.signing.key.password="${KEY_PASS:-placeholder}" \
    assembleRelease 2>&1 | tee "$LOG" | tail -80
GRADLE_EXIT=${PIPESTATUS[0]}
set -e; set -o pipefail
tail -200 "$LOG" > _artifacts/wff-gradle-tail.txt 2>/dev/null || true

APP_VERSION=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
BUILD_TS=$(date -u +%Y%m%d-%H%M)
SUFFIX="v${APP_VERSION}-${BUILD_TS}"
find app/build/outputs -name "*.apk" -exec cp {} "_artifacts/servia-wff-${SUFFIX}.apk" \; 2>&1 || true
echo "$SUFFIX" > _artifacts/WFF_BUILD_INFO.txt

# Also stash a stable filename so the wf-pusher build can find it
find app/build/outputs -name "*.apk" -exec cp {} "_artifacts/burjsunset.apk" \; 2>&1 || true

ls -la _artifacts/

if [ "$GRADLE_EXIT" != "0" ]; then exit "$GRADLE_EXIT"; fi
if [ -z "$(ls _artifacts/servia-wff-${SUFFIX}.apk 2>/dev/null)" ]; then
  echo "::error::WFF face produced 0 APK"
  exit 1
fi
