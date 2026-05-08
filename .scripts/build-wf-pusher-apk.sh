#!/usr/bin/env bash
# v1.24.54 — Build the Servia Watch Face Pusher APK (Wear OS).
#
# Bundles the wff-only payload built by build-wff-only-apk.sh into
# res/raw/payload.apk, then assembles a Wear OS APK that calls
# androidx.wear.watchface.push.WatchFacePushManager#addWatchFace on the
# bundled payload.
#
# REQUIREMENT: build-wff-only-apk.sh must run first — its output APK
# gets copied into our res/raw/ before assembly.
#
# Output: twa/android/wf-pusher-build/_artifacts/servia-wf-pusher-vNN-TS.apk

set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

SRC="twa/android/wf-pusher"
WEAR_SRC="twa/android/wear"
BUILD_DIR="twa/android/wf-pusher-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

PAYLOAD_SRC="twa/android/wff-only-build/_artifacts/payload.apk"
if [ ! -f "$PAYLOAD_SRC" ]; then
  echo "::error::wff-only payload not found at $PAYLOAD_SRC"
  echo "::error::Run .scripts/build-wff-only-apk.sh first"
  exit 1
fi

echo "=== Setting up wf-pusher project at $BUILD_DIR ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/pusher"
mkdir -p "$BUILD_DIR/app/src/main/res/raw"
mkdir -p "$BUILD_DIR/app/src/main/res/layout"
mkdir -p "$BUILD_DIR/app/src/main/res/values"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-hdpi"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-xhdpi"

cp -v "$SRC/AndroidManifest.xml"          "$BUILD_DIR/app/src/main/AndroidManifest.xml"
cp -v "$SRC/java/ae/servia/pusher/"*.java "$BUILD_DIR/app/src/main/java/ae/servia/pusher/"
cp -v "$SRC/res-layout/"*.xml             "$BUILD_DIR/app/src/main/res/layout/"
cp -v "$SRC/res-values/"*.xml             "$BUILD_DIR/app/src/main/res/values/"
cp -v "$PAYLOAD_SRC"                      "$BUILD_DIR/app/src/main/res/raw/payload.apk"

ICON_SRC="web/brand/servia-icon-512x512.png"
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-hdpi/wear_ic_launcher.png"
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-xhdpi/wear_ic_launcher.png"
fi

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
cp -v "$SRC/build.gradle" "$BUILD_DIR/app/build.gradle"

APP_VER=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
if [ -n "$APP_VER" ]; then
  sed -i -E "s/versionName \"[^\"]*\"/versionName \"$APP_VER\"/" "$BUILD_DIR/app/build.gradle"
  echo "Injected versionName = $APP_VER"
fi

GW_DIR="twa/android/generated"
if [ -d "$GW_DIR/gradle/wrapper" ]; then
  mkdir -p "$BUILD_DIR/gradle/wrapper"
  cp -r "$GW_DIR/gradle/wrapper/." "$BUILD_DIR/gradle/wrapper/"
  cp "$GW_DIR/gradlew" "$BUILD_DIR/gradlew"
  cp "$GW_DIR/gradlew.bat" "$BUILD_DIR/gradlew.bat" 2>/dev/null || true
  chmod +x "$BUILD_DIR/gradlew"
else
  echo "ERROR: no gradle wrapper to borrow"
  exit 1
fi

cat > "$BUILD_DIR/gradle.properties" <<'PROPS'
android.useAndroidX=true
android.enableJetifier=false
org.gradle.jvmargs=-Xmx2048m
android.suppressUnsupportedCompileSdk=34
PROPS

echo ""
echo "=== Building wf-pusher APK ==="
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/pusher-gradle.log
set +e
./gradlew --no-daemon --stacktrace --info \
    -Pandroid.injected.signing.store.file="$KS_PATH" \
    -Pandroid.injected.signing.store.password="${KEYSTORE_PASS:-placeholder}" \
    -Pandroid.injected.signing.key.alias="${KEY_ALIAS:-servia}" \
    -Pandroid.injected.signing.key.password="${KEY_PASS:-placeholder}" \
    assembleRelease 2>&1 | tee "$LOG" | tail -150
GRADLE_EXIT=${PIPESTATUS[0]}
set -e
echo "=== wf-pusher gradle exit: $GRADLE_EXIT ==="
tail -400 "$LOG" > _artifacts/pusher-gradle-tail.txt 2>/dev/null || true

APP_VERSION="$APP_VER"
BUILD_TS=$(date -u +%Y%m%d-%H%M)
SUFFIX="v${APP_VERSION}-${BUILD_TS}"
find app/build/outputs -name "*.apk" -exec cp {} "_artifacts/servia-wf-pusher-${SUFFIX}.apk" \; 2>&1 || true
echo "$SUFFIX" > _artifacts/PUSHER_BUILD_INFO.txt

# Pull the wff-only payload artifact in too so a single artifact ZIP
# contains both APKs (Bugjaeger workflow needs them side-by-side).
cp -v "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/twa/android/wff-only-build/_artifacts/"servia-wff-burj-sunset-*.apk \
      _artifacts/ 2>/dev/null || true

ls -la _artifacts/

if [ "$GRADLE_EXIT" != "0" ]; then
  echo "::error::wf-pusher build FAILED with exit $GRADLE_EXIT"
  exit "$GRADLE_EXIT"
fi
if [ -z "$(ls _artifacts/servia-wf-pusher-${SUFFIX}.apk 2>/dev/null)" ]; then
  echo "::error::wf-pusher gradle returned 0 but produced NO APK"
  exit 1
fi
