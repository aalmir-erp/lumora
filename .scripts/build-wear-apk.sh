#!/usr/bin/env bash
# Build the Servia Wear OS standalone APK.
#
# Wear OS app source lives at twa/android/wear/. We assemble a minimal
# standalone Android project around it (top-level build.gradle,
# settings.gradle, gradle wrapper) and then `gradlew bundleRelease
# assembleRelease` produces a signed APK + AAB.
#
# Output: twa/android/wear-build/_artifacts/{servia-wear.apk, servia-wear.aab}
set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

WEAR_SRC="twa/android/wear"
BUILD_DIR="twa/android/wear-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

echo "=== Setting up Wear OS gradle project at $BUILD_DIR ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/wear"
mkdir -p "$BUILD_DIR/app/src/main/res/layout"
mkdir -p "$BUILD_DIR/app/src/main/res/values"
mkdir -p "$BUILD_DIR/app/src/main/res/drawable"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-hdpi"
mkdir -p "$BUILD_DIR/app/src/main/res/mipmap-xhdpi"

# Source files
mkdir -p "$BUILD_DIR/app/src/main/java/ae/servia/wear/tiles"
cp -v "$WEAR_SRC/AndroidManifest.xml" "$BUILD_DIR/app/src/main/AndroidManifest.xml"
# Copy ALL java files (root + tiles subpackage)
cp -v "$WEAR_SRC/java/"*.java "$BUILD_DIR/app/src/main/java/ae/servia/wear/" 2>/dev/null || true
cp -v "$WEAR_SRC/java/tiles/"*.java "$BUILD_DIR/app/src/main/java/ae/servia/wear/tiles/" 2>/dev/null || true
cp -v "$WEAR_SRC/res-layout/wear_main.xml" "$BUILD_DIR/app/src/main/res/layout/"
cp -v "$WEAR_SRC/res-values/strings.xml" "$BUILD_DIR/app/src/main/res/values/"
cp -v "$WEAR_SRC/res-values/styles.xml" "$BUILD_DIR/app/src/main/res/values/"
# v1.24.14 — copy ALL drawable XMLs **and** PNGs (tile previews now bitmap-
# only because Samsung's tile picker silently rejects drawable XMLs).
cp -v "$WEAR_SRC/res-drawable/"*.xml "$BUILD_DIR/app/src/main/res/drawable/" 2>/dev/null || true
cp -v "$WEAR_SRC/res-drawable/"*.png "$BUILD_DIR/app/src/main/res/drawable/" 2>/dev/null || true

# Use the same Servia icon bytes for the launcher (256x256 plenty for hdpi/xhdpi)
# We'll just copy the existing servia-icon-512x512.png into the mipmap dirs.
ICON_SRC="web/brand/servia-icon-512x512.png"
if [ -f "$ICON_SRC" ]; then
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-hdpi/wear_ic_launcher.png"
  cp "$ICON_SRC" "$BUILD_DIR/app/src/main/res/mipmap-xhdpi/wear_ic_launcher.png"
fi

# Top-level build.gradle (project)
cat > "$BUILD_DIR/build.gradle" <<'GRADLE'
buildscript {
    repositories { google(); mavenCentral() }
    dependencies { classpath 'com.android.tools.build:gradle:8.5.2' }
}
allprojects { repositories { google(); mavenCentral() } }
GRADLE

# settings.gradle
cat > "$BUILD_DIR/settings.gradle" <<'GRADLE'
rootProject.name = "servia-wear"
include ':app'
GRADLE

# Module build.gradle
cp -v "$WEAR_SRC/build.gradle" "$BUILD_DIR/app/build.gradle"

# Gradle wrapper — copy from the TWA-generated project so we don't need a separate download
GRADLE_DIR="twa/android/generated"
if [ -d "$GRADLE_DIR/gradle/wrapper" ]; then
  mkdir -p "$BUILD_DIR/gradle/wrapper"
  cp -r "$GRADLE_DIR/gradle/wrapper/." "$BUILD_DIR/gradle/wrapper/"
  cp "$GRADLE_DIR/gradlew" "$BUILD_DIR/gradlew"
  cp "$GRADLE_DIR/gradlew.bat" "$BUILD_DIR/gradlew.bat" 2>/dev/null || true
  chmod +x "$BUILD_DIR/gradlew"
else
  echo "ERROR: TWA project not generated yet, can't borrow gradle wrapper"
  exit 1
fi

# gradle.properties — match the TWA project's targetSDK / android.useAndroidX
cat > "$BUILD_DIR/gradle.properties" <<'PROPS'
android.useAndroidX=true
android.enableJetifier=false
org.gradle.jvmargs=-Xmx2048m
android.suppressUnsupportedCompileSdk=34
PROPS

echo ""
echo "=== Building Wear OS APK ==="
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/wear-gradle.log
# CRITICAL: disable `set -e`/`pipefail` for the gradle invocation. Otherwise
# the script aborts on the first non-zero exit BEFORE we get a chance to
# capture the log and write diagnostics. Was the root cause of the
# "wear-gradle-tail.txt missing -> log push skipped" loop.
set +e
set +o pipefail
./gradlew --no-daemon --stacktrace --info \
    -Pandroid.injected.signing.store.file="$KS_PATH" \
    -Pandroid.injected.signing.store.password="${KEYSTORE_PASS}" \
    -Pandroid.injected.signing.key.alias="${KEY_ALIAS}" \
    -Pandroid.injected.signing.key.password="${KEY_PASS}" \
    bundleRelease assembleRelease 2>&1 | tee "$LOG" | tail -150
GRADLE_EXIT=${PIPESTATUS[0]}
set -e
set -o pipefail
echo ""
echo "=== gradle exit code: $GRADLE_EXIT ==="
echo "=== full log saved to $BUILD_DIR/$LOG ==="

# Always copy a trimmed last-300-lines tail in case the full log gets truncated
tail -300 "$LOG" > _artifacts/wear-gradle-tail.txt 2>/dev/null || true

echo ""
echo "=== Build outputs (everything matching apk/aab) ==="
find app/build -type f \( -name "*.apk" -o -name "*.aab" \) 2>/dev/null > _artifacts/wear-found.txt || true
cat _artifacts/wear-found.txt
echo ""
echo "=== Output dir tree (first 40 dirs) ==="
find app/build -type d 2>/dev/null | head -40 > _artifacts/wear-dirtree.txt || true
cat _artifacts/wear-dirtree.txt

# Try to copy artefacts even if gradle reported non-zero (some configs
# produce a partial APK that still installs)
find app/build/outputs -name "*.apk" -exec cp {} _artifacts/servia-wear-signed.apk \; 2>&1 || true
find app/build/outputs -name "*.aab" -exec cp {} _artifacts/servia-wear-bundle.aab \; 2>&1 || true
ls -la _artifacts/

if [ "$GRADLE_EXIT" != "0" ]; then
  echo "::error::Wear OS gradle build FAILED with exit $GRADLE_EXIT — see _artifacts/wear-gradle-tail.txt"
  exit "$GRADLE_EXIT"
fi
if [ ! -f _artifacts/servia-wear-signed.apk ]; then
  echo "::error::Wear OS gradle returned 0 but produced NO APK — see _artifacts/wear-gradle-tail.txt"
  exit 1
fi
