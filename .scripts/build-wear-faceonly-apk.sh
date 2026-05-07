#!/usr/bin/env bash
# v1.24.43 — Build the standalone Servia Faces APK.
#
# Reuses the watchface Java sources from twa/android/wear/java/watchface/
# but ships them in a brand-new package (ae.servia.wear.faces) with no
# tiles, no activities besides a tiny launcher. Used as an A/B test —
# if THIS picker entry shows up but the main Servia Wear's doesn't, it
# means co-packaging with non-face activities was the cause.
#
# Output: twa/android/wear-faceonly-build/_artifacts/{servia-faces-vNN-TS.apk, .aab}

set -euo pipefail
cd "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}"

SRC="twa/android/wear-faceonly"
WEAR_SRC="twa/android/wear"
BUILD_DIR="twa/android/wear-faceonly-build"
KS_PATH="${1:-${RUNNER_TEMP:-/tmp}/servia.jks}"

echo "=== Setting up Servia Faces standalone gradle project at $BUILD_DIR ==="
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
# Splice in the 22 service entries (kept under tools/watchface/)
FRAGMENT="$WEAR_SRC/tools-manifest_entries.xml"
if [ ! -f "$FRAGMENT" ]; then
  # Fallback: if the fragment isn't checked in, generate it inline
  python3 <<'PYEOF'
import os, re, json, glob, sys
sys.path.insert(0, ".")

# Load metadata (regenerate if missing)
meta_file = "twa/android/wear/tools-metadata.json"
if not os.path.exists(meta_file):
    print("ERROR: missing tools-metadata.json — run tools/watchface/generate.py")
    sys.exit(1)

meta = json.loads(open(meta_file).read())
ids = sorted(meta.keys(), key=lambda s: int(re.match(r'p(\d+)', s).group(1)))

# pretty names
NAMES = {
    "p1_burj_sunset":"Burj Sunset","p2_marina_neon":"Marina Neon",
    "p3_desert_premium":"Desert Premium","p4_sport_pulse":"Sport Pulse",
    "p5_emergency_red":"Emergency Red","p6_modular_dark":"Modular Pro",
    "p7_neon_grid":"Neon Grid","p8_calligraphy_gold":"Calligraphy Gold",
    "p9_pearl_ladies":"Pearl Ladies","p10_eco_botanical":"Eco Botanical",
    "p11_minimal_white":"Minimal White","p12_falcon_premium":"Falcon Premium",
    "p13_pixel_retro":"Pixel Retro","p14_carbon_fiber":"Carbon Fiber",
    "p15_kids_fun":"Kids Fun","p16_business_exec":"Business Exec",
    "p17_sandstorm_premium":"Sandstorm Premium","p18_violet_chrono":"Violet Chronograph",
    "p19_ocean_animated":"Ocean Live","p20_aviation":"Aviation",
    "p21_servia_hours":"Servia Hours","p22_servia_dial":"Servia Dial",
}

frag = ""
for i, fid in enumerate(ids, 1):
    pid_pad = f"{i:02d}"
    classname = f"ServiaFace{pid_pad}{fid.split('_',1)[1].title().replace('_','')}"
    nm = NAMES.get(fid, fid)
    frag += f'''
        <service
            android:name="ae.servia.wear.watchface.{classname}"
            android:label="Servia · {nm}"
            android:permission="android.permission.BIND_WALLPAPER"
            android:directBootAware="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.service.wallpaper.WallpaperService" />
                <category android:name="com.google.android.wearable.watchface.category.WATCH_FACE" />
            </intent-filter>
            <meta-data
                android:name="com.google.android.wearable.watchface.preview"
                android:resource="@drawable/wf_preview_p{pid_pad}" />
            <meta-data
                android:name="com.google.android.wearable.watchface.preview_circular"
                android:resource="@drawable/wf_preview_p{pid_pad}" />
            <meta-data
                android:name="android.service.wallpaper"
                android:resource="@xml/watch_face" />
        </service>
'''
open("/tmp/_face_fragment.xml","w").write(frag)
PYEOF
  FRAGMENT="/tmp/_face_fragment.xml"
fi

# Splice fragment into manifest at the placeholder
python3 - <<PYEOF
src = open("$BUILD_DIR/app/src/main/AndroidManifest.xml").read()
frag = open("$FRAGMENT").read()
new = src.replace("<!-- @SERVIA_FACE_SERVICES@ -->", frag)
open("$BUILD_DIR/app/src/main/AndroidManifest.xml","w").write(new)
PYEOF

# ---- Java sources ----
# Watchface package (BaseServiaWatchFaceService + WatchFaceMeta + WatchFaceRegistry + 22 ServiaFaceNN.java)
cp -v "$WEAR_SRC/java/watchface/"*.java "$BUILD_DIR/app/src/main/java/ae/servia/wear/watchface/"
# WatchHomepageBridge (used by BaseServiaWatchFaceService for fallback open)
cp -v "$WEAR_SRC/java/WatchHomepageBridge.java" "$BUILD_DIR/app/src/main/java/ae/servia/wear/" || true
# LauncherActivity
cp -v "$SRC/LauncherActivity.java" "$BUILD_DIR/app/src/main/java/ae/servia/wear/faces/"

# ---- Resources ----
# Strings
cp -v "$SRC/strings.xml" "$BUILD_DIR/app/src/main/res/values/strings.xml"
# Drawables: bring ALL wf_*.png (frame + preview)
cp -v "$WEAR_SRC/res-drawable/"wf_*.png "$BUILD_DIR/app/src/main/res/drawable/" 2>/dev/null || true
cp -v "$WEAR_SRC/res-drawable/"tile_preview_hub.png "$BUILD_DIR/app/src/main/res/drawable/" 2>/dev/null || true
# Wallpaper descriptor
cp -v "$WEAR_SRC/res-xml/watch_face.xml" "$BUILD_DIR/app/src/main/res/xml/"
# Launcher icon
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
rootProject.name = "servia-faces"
include ':app'
GRADLE
cp -v "$SRC/build.gradle" "$BUILD_DIR/app/build.gradle"

# Reuse the gradle wrapper from the TWA-generated project
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
echo "=== Building Servia Faces APK ==="
cd "$BUILD_DIR"
mkdir -p _artifacts
LOG=_artifacts/faces-gradle.log
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
echo "=== faces gradle exit: $GRADLE_EXIT ==="
tail -300 "$LOG" > _artifacts/faces-gradle-tail.txt 2>/dev/null || true

echo "=== Faces build outputs ==="
find app/build -type f \( -name "*.apk" -o -name "*.aab" \) 2>/dev/null > _artifacts/faces-found.txt || true
cat _artifacts/faces-found.txt

# Versioned filename
APP_VERSION=$(grep -E 'APP_VERSION\s*=' "${GITHUB_WORKSPACE:-/tmp/lumora-deploy}/app/config.py" | head -1 | sed -E 's/.*"([^"]+)".*/\1/')
BUILD_TS=$(date -u +%Y%m%d-%H%M)
SUFFIX="v${APP_VERSION}-${BUILD_TS}"
find app/build/outputs -name "*.apk" -exec cp {} _artifacts/servia-faces-signed.apk \; 2>&1 || true
find app/build/outputs -name "*.aab" -exec cp {} _artifacts/servia-faces-bundle.aab \; 2>&1 || true
[ -f _artifacts/servia-faces-signed.apk ] && cp _artifacts/servia-faces-signed.apk "_artifacts/servia-faces-${SUFFIX}.apk"
[ -f _artifacts/servia-faces-bundle.aab ] && cp _artifacts/servia-faces-bundle.aab "_artifacts/servia-faces-${SUFFIX}.aab"
echo "$SUFFIX" > _artifacts/FACES_BUILD_INFO.txt
ls -la _artifacts/

echo "=== Faces build dir tree (debug) ==="
find . -type f \( -name "*.apk" -o -name "*.aab" -o -name "AndroidManifest.xml" \) 2>/dev/null | head -20 > _artifacts/faces-found.txt
cat _artifacts/faces-found.txt
echo "=== app/build/outputs (recursive) ==="
find app/build/outputs -type f 2>/dev/null | head -40 >> _artifacts/faces-found.txt || true
cat _artifacts/faces-found.txt

if [ "$GRADLE_EXIT" != "0" ]; then
  echo "::warning::Servia Faces gradle build FAILED with exit $GRADLE_EXIT"
  exit "$GRADLE_EXIT"
fi
if [ ! -f _artifacts/servia-faces-signed.apk ]; then
  echo "::error::Servia Faces gradle returned 0 but produced NO APK"
  echo "::error::See _artifacts/faces-gradle-tail.txt + faces-tree.txt for details"
  exit 1
fi
