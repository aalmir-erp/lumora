#!/usr/bin/env bash
# v1.24.43 — Servia Single Face APK (minimum-viable diagnostic build).
#
# Bundles ONLY the ServiaFace01BurjSunset service plus the launcher
# diagnostic activity. Different applicationId from the multi-face
# standalone (ae.servia.wear.single vs ae.servia.wear.faces) so all
# three APKs install alongside each other.
#
# Output: twa/android/wear-singleface-build/_artifacts/servia-single-face-vNN-TS.apk

set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

SRC="twa/android/wear-singleface"
WEAR_SRC="twa/android/wear"
FACE_SRC="twa/android/wear-faceonly"
BUILD_DIR="twa/android/wear-singleface-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

echo "=== Setting up Servia Single Face gradle project at $BUILD_DIR ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/wear"
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface"
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/wear/faces"
mkdir -p "$BUILD_DIR/app/src/main/res/values"
mkdir -p "$BUILD_DIR/app/src/main/res/drawable"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-hdpi"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-xhdpi"
mkdir -p "$BUILD_DIR/app/src/main/res/xml"

# ---- Manifest ----
cp -v "$SRC/AndroidManifest.xml" "$BUILD_DIR/app/src/main/AndroidManifest.xml"

# ---- Java sources (minimal — only what's needed for ONE face) ----
# ONLY new-architecture files. Skipping legacy WatchFacePreset/
# WatchFaceSlots/WatchFaceEditorActivity/ThemePicker which depend on
# ae.servia.wear.ServiaTheme that's outside this APK's namespace.
cp -v "$WEAR_SRC/java/watchface/BaseServiaWatchFaceService.java" "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface/"
cp -v "$WEAR_SRC/java/watchface/WatchFaceMeta.java"               "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface/"
cp -v "$WEAR_SRC/java/watchface/WatchFaceRegistry.java"           "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface/"
cp -v "$WEAR_SRC/java/watchface/ServiaWearLog.java"               "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface/"
cp -v "$WEAR_SRC/java/watchface/"ServiaFace*.java                 "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface/"
# WatchHomepageBridge
cp -v "$WEAR_SRC/java/WatchHomepageBridge.java" "$BUILD_DIR/app/src/main/java/ae/servia/wear/" 2>/dev/null || true
# Reuse the diagnostic LauncherActivity from the face-only standalone
cp -v "$FACE_SRC/LauncherActivity.java" "$BUILD_DIR/app/src/main/java/ae/servia/wear/faces/"

# ---- Resources ----
cp -v "$FACE_SRC/strings.xml" "$BUILD_DIR/app/src/main/res/values/strings.xml" 2>/dev/null || true
cp -v "$WEAR_SRC/res-drawable/"wf_*.png "$BUILD_DIR/app/src/main/res/drawable/" 2>/dev/null || true
cp -v "$WEAR_SRC/res-drawable/"tile_preview_hub.png "$BUILD_DIR/app/src/main/res/drawable/" 2>/dev/null || true
cp -v "$WEAR_SRC/res-xml/watch_face.xml" "$BUILD_DIR/app/src/main/res/xml/"
# v1.24.45 — WFF XML resources (face 1 only for single-face APK, but
# safer to copy all so the manifest can opt-in to any of them)
mkdir -p "$BUILD_DIR/app/src/main/res/raw"
cp -v "$WEAR_SRC/res-raw/"*.xml "$BUILD_DIR/app/src/main/res/raw/" 2>/dev/null || true
ICON_SRC="web/brand/servia-icon-512x512.png"
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-hdpi/wear_ic_launcher.png"
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-xhdpi/wear_ic_launcher.png"
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
rootProject.name = "servia-single-face"
include ':app'
GRADLE
cp -v "$SRC/build.gradle" "$BUILD_DIR/app/build.gradle"
# v1.24.50 — inject live APP_VERSION into versionName.
APP_VER=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
if [ -n "$APP_VER" ]; then
  sed -i -E "s/versionName \"[^\"]*\"/versionName \"$APP_VER\"/" "$BUILD_DIR/app/build.gradle"
  echo "Injected versionName = $APP_VER into single-face build.gradle"
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

# ---- Build ----
echo ""
echo "=== Building Servia Single Face APK ==="
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/single-gradle.log
set +e
set +o pipefail
./gradlew --no-daemon --stacktrace --info \
    -Pandroid.injected.signing.store.file="$KS_PATH" \
    -Pandroid.injected.signing.store.password="${KEYSTORE_PASS:-placeholder}" \
    -Pandroid.injected.signing.key.alias="${KEY_ALIAS:-servia}" \
    -Pandroid.injected.signing.key.password="${KEY_PASS:-placeholder}" \
    bundleRelease assembleRelease 2>&1 | tee "$LOG" | tail -120
GRADLE_EXIT=${PIPESTATUS[0]}
set -e
set -o pipefail
echo "=== single gradle exit: $GRADLE_EXIT ==="
tail -300 "$LOG" > _artifacts/single-gradle-tail.txt 2>/dev/null || true

APP_VERSION=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
BUILD_TS=$(date -u +%Y%m%d-%H%M)
SUFFIX="v${APP_VERSION}-${BUILD_TS}"
# v1.24.48 — versioned filenames only.
find app/build/outputs -name "*.apk" -exec cp {} "_artifacts/servia-single-face-${SUFFIX}.apk" \; 2>&1 || true
find app/build/outputs -name "*.aab" -exec cp {} "_artifacts/servia-single-face-${SUFFIX}.aab" \; 2>&1 || true
echo "$SUFFIX" > _artifacts/SINGLE_BUILD_INFO.txt
ls -la _artifacts/

echo "=== Single Face build dir tree (debug) ==="
find . -type f \( -name "*.apk" -o -name "*.aab" -o -name "AndroidManifest.xml" \) 2>/dev/null | head -20 > _artifacts/single-found.txt
cat _artifacts/single-found.txt
echo "=== app/build/outputs (recursive) ==="
find app/build/outputs -type f 2>/dev/null | head -40 >> _artifacts/single-found.txt || true
cat _artifacts/single-found.txt

if [ "$GRADLE_EXIT" != "0" ]; then
  echo "::warning::Servia Single Face build FAILED with exit $GRADLE_EXIT"
  exit "$GRADLE_EXIT"
fi
if [ -z "$(ls _artifacts/servia-single-face-${SUFFIX}.apk 2>/dev/null)" ]; then
  echo "::error::Servia Single Face gradle returned 0 but produced NO APK"
  echo "::error::See _artifacts/single-gradle-tail.txt + single-tree.txt for details"
  exit 1
fi
