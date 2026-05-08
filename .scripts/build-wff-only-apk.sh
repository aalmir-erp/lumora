#!/usr/bin/env bash
# v1.24.54 — Build the Servia WFF-only payload APK (Burj Sunset).
#
# This APK has NO Java/Kotlin code (android:hasCode="false"). It is the
# "package" handed off to the Watch Face Push API by the wf-pusher
# companion app. Build it FIRST so build-wf-pusher-apk.sh can drop it
# into the pusher's res/raw before assembling.
#
# Output: twa/android/wff-only-build/_artifacts/servia-wff-burj-sunset-vNN-TS.apk

set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

SRC="twa/android/wff-only"
BUILD_DIR="twa/android/wff-only-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

echo "=== Setting up wff-only project at $BUILD_DIR ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app/src/main/res/raw"
mkdir -p "$BUILD_DIR/app/src/main/res/drawable"
mkdir -p "$BUILD_DIR/app/src/main/res/values"

cp -v "$SRC/AndroidManifest.xml" "$BUILD_DIR/app/src/main/AndroidManifest.xml"
cp -v "$SRC/res-raw/"*.xml       "$BUILD_DIR/app/src/main/res/raw/"
cp -v "$SRC/res-drawable/"*.png  "$BUILD_DIR/app/src/main/res/drawable/"
cp -v "$SRC/res-values/"*.xml    "$BUILD_DIR/app/src/main/res/values/"

cat > "$BUILD_DIR/build.gradle" <<'GRADLE'
buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.5.2' }
}
allprojects { repositories { google(); mavenCentral() } }
GRADLE
cat > "$BUILD_DIR/settings.gradle" <<'GRADLE'
rootProject.name = "servia-wff-only"
include ':app'
GRADLE
cp -v "$SRC/build.gradle" "$BUILD_DIR/app/build.gradle"

# Inject live APP_VERSION into versionName.
APP_VER=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
if [ -n "$APP_VER" ]; then
  sed -i -E "s/versionName \"[^\"]*\"/versionName \"$APP_VER\"/" "$BUILD_DIR/app/build.gradle"
  echo "Injected versionName = $APP_VER"
fi

# Borrow the gradle wrapper from the main twa build.
GW_DIR="twa/android/generated"
if [ -d "$GW_DIR/gradle/wrapper" ]; then
  mkdir -p "$BUILD_DIR/gradle/wrapper"
  cp -r "$GW_DIR/gradle/wrapper/." "$BUILD_DIR/gradle/wrapper/"
  cp "$GW_DIR/gradlew" "$BUILD_DIR/gradlew"
  cp "$GW_DIR/gradlew.bat" "$BUILD_DIR/gradlew.bat" 2>/dev/null || true
  chmod +x "$BUILD_DIR/gradlew"
else
  echo "ERROR: no gradle wrapper to borrow (run phone build first)"
  exit 1
fi

cat > "$BUILD_DIR/gradle.properties" <<'PROPS'
android.useAndroidX=true
android.enableJetifier=false
org.gradle.jvmargs=-Xmx2048m
android.suppressUnsupportedCompileSdk=34
PROPS

echo ""
echo "=== Building wff-only APK ==="
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/wff-gradle.log
set +e
./gradlew --no-daemon --stacktrace --info \
    -Pandroid.injected.signing.store.file="$KS_PATH" \
    -Pandroid.injected.signing.store.password="${KEYSTORE_PASS:-placeholder}" \
    -Pandroid.injected.signing.key.alias="${KEY_ALIAS:-servia}" \
    -Pandroid.injected.signing.key.password="${KEY_PASS:-placeholder}" \
    assembleRelease 2>&1 | tee "$LOG" | tail -120
GRADLE_EXIT=${PIPESTATUS[0]}
set -e
echo "=== wff-only gradle exit: $GRADLE_EXIT ==="
tail -300 "$LOG" > _artifacts/wff-gradle-tail.txt 2>/dev/null || true

APP_VERSION="$APP_VER"
BUILD_TS=$(date -u +%Y%m%d-%H%M)
SUFFIX="v${APP_VERSION}-${BUILD_TS}"
find app/build/outputs -name "*.apk" -exec cp {} "_artifacts/servia-wff-burj-sunset-${SUFFIX}.apk" \; 2>&1 || true
echo "$SUFFIX" > _artifacts/WFF_BUILD_INFO.txt

# Stage payload for the pusher build to pick up.
mkdir -p ../wf-pusher-build/app/src/main/res/raw
PAYLOAD=$(find _artifacts -name "servia-wff-burj-sunset-*.apk" | head -1 || true)
if [ -n "$PAYLOAD" ]; then
  cp -v "$PAYLOAD" "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/twa/android/wff-only-build/_artifacts/payload.apk"
  echo "Payload staged at _artifacts/payload.apk for pusher build."
fi

ls -la _artifacts/

if [ "$GRADLE_EXIT" != "0" ]; then
  echo "::error::wff-only build FAILED with exit $GRADLE_EXIT"
  exit "$GRADLE_EXIT"
fi
if [ -z "$(ls _artifacts/servia-wff-burj-sunset-${SUFFIX}.apk 2>/dev/null)" ]; then
  echo "::error::wff-only gradle returned 0 but produced NO APK"
  exit 1
fi
