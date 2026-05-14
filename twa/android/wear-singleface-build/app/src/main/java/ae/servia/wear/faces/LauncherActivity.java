package ae.servia.wear.faces;

import android.app.Activity;
import android.app.WallpaperManager;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.pm.ServiceInfo;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import ae.servia.wear.watchface.ServiaWearLog;

/**
 * v1.24.47 — Servia Faces standalone-APK launcher with full diagnostics +
 * action buttons.
 *
 * NEW IN v1.24.47:
 *   - "▶ APPLY THIS FACE NOW" button: fires
 *     WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER for ServiaFace01,
 *     opens the system's wallpaper preview where you tap "Set wallpaper"
 *     to actually apply the face. This is the standard supported way for
 *     a third-party app to apply its watch face on user devices, vs Wear
 *     Installer 2's developer-only DEBUG_SURFACE broadcast which is
 *     rejected on Wear OS 5+/Samsung One UI.
 *
 *   - "📤 SEND LOG TO SERVIA" button: POSTs the diagnostic dump
 *     (PackageManager scan + log file tail) to /api/wear/diag-log on the
 *     server. This lets Claude read the user's watch state directly
 *     without ADB access — exactly what was missing before.
 */
public class LauncherActivity extends Activity {

    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());
    private TextView sendStatusView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(16, 24, 16, 20);
        sv.addView(root);
        setContentView(sv);

        addHeader(root, "SERVIA FACES", 0xFFFCD34D);
        addSpacer(root, 4);

        // BIG version banner so the user always knows what's installed
        try {
            android.content.pm.PackageInfo pi = getPackageManager().getPackageInfo(getPackageName(), 0);
            TextView ver = new TextView(this);
            ver.setText("v" + pi.versionName);
            ver.setTextColor(0xFFA7F3D0);
            ver.setTextSize(28);
            ver.setTypeface(ver.getTypeface(), Typeface.BOLD);
            ver.setGravity(Gravity.CENTER);
            ver.setPadding(0, 4, 0, 4);
            root.addView(ver);
        } catch (Throwable ignored) {}
        addSpacer(root, 8);

        // ==== ACTIONS (top, big, can't miss) =========================
        // v1.24.52 PLAN B: two Apply buttons to A/B test which face type
        // Samsung's One UI Watch picker accepts.
        addActionButton(root, "▶ APPLY (LEGACY)", 0xFF065F46, 0xFFFFFFFF,
            v -> applyFace("ae.servia.wear.watchface.LegacyServiaFace01"));
        addSpacer(root, 4);
        addActionButton(root, "▶ APPLY (ANDROIDX)", 0xFFFCD34D, 0xFF1F1411,
            v -> applyFace("ae.servia.wear.watchface.ServiaFace01BurjSunset"));
        addSpacer(root, 6);
        addActionButton(root, "📤 SEND LOG TO SERVIA", 0xFF065F46, 0xFFFFFFFF,
            v -> sendLog());

        sendStatusView = new TextView(this);
        sendStatusView.setText("");
        sendStatusView.setTextColor(0xFFA7F3D0);
        sendStatusView.setTextSize(10);
        sendStatusView.setGravity(Gravity.CENTER);
        sendStatusView.setPadding(0, 6, 0, 8);
        root.addView(sendStatusView);

        addSpacer(root, 4);
        addBody(root,
            "Apply: opens system wallpaper preview · tap 'Set' there to install face\n"
          + "Send Log: POSTs diagnostic to servia.ae for remote support\n",
            0xFFCBD5E1);
        addSpacer(root, 8);

        // ==== DIAGNOSTICS ============================================
        addHeader(root, "DIAGNOSTICS", 0xFFFCD34D);
        addSpacer(root, 4);
        try {
            String pkg = getPackageName();
            android.content.pm.PackageInfo pi = getPackageManager().getPackageInfo(pkg, 0);
            addRow(root, "App version", pi.versionName + " (" + pi.versionCode + ")", 0xFFA7F3D0);
            addRow(root, "App package", pkg, 0xFFCBD5E1);
            addRow(root, "Target SDK", String.valueOf(getApplicationInfo().targetSdkVersion), 0xFFCBD5E1);
        } catch (Throwable t) {
            addRow(root, "App info", "ERROR: " + t.getMessage(), 0xFFFCA5A5);
        }
        addRow(root, "Android SDK", String.valueOf(Build.VERSION.SDK_INT) + " (" + Build.VERSION.RELEASE + ")", 0xFFCBD5E1);
        addRow(root, "Watch model", Build.MANUFACTURER + " " + Build.MODEL, 0xFFCBD5E1);
        addRow(root, "Build fingerprint", clip(Build.FINGERPRINT, 40), 0xFF94A3B8);

        addSpacer(root, 8);

        try {
            android.content.pm.PackageInfo pi = getPackageManager().getPackageInfo(
                getPackageName(), PackageManager.GET_SERVICES);
            int faceServices = 0;
            if (pi.services != null) {
                for (ServiceInfo s : pi.services) {
                    if (s.permission != null && s.permission.contains("BIND_WALLPAPER")) {
                        faceServices++;
                    }
                }
            }
            int color = faceServices > 0 ? 0xFFA7F3D0 : 0xFFFCA5A5;
            addRow(root, "Faces declared", String.valueOf(faceServices) + " service(s)", color);
        } catch (Throwable t) {
            addRow(root, "Faces declared", "ERROR: " + t.getMessage(), 0xFFFCA5A5);
        }

        try {
            Intent wfIntent = new Intent("android.service.wallpaper.WallpaperService");
            wfIntent.addCategory("com.google.android.wearable.watchface.category.WATCH_FACE");
            List<ResolveInfo> resolved = getPackageManager().queryIntentServices(wfIntent, 0);
            int sysCount = resolved == null ? 0 : resolved.size();
            int color = sysCount > 0 ? 0xFFA7F3D0 : 0xFFFCA5A5;
            addRow(root, "Faces visible to system", String.valueOf(sysCount), color);

            if (resolved != null && !resolved.isEmpty()) {
                addSpacer(root, 4);
                addBody(root, "Found in system:", 0xFF94A3B8);
                for (ResolveInfo ri : resolved) {
                    String pkg = ri.serviceInfo != null ? ri.serviceInfo.packageName : "?";
                    String name = ri.serviceInfo != null ? ri.serviceInfo.name : "?";
                    String shortName = name;
                    int dot = name.lastIndexOf('.');
                    if (dot > 0) shortName = name.substring(dot + 1);
                    int color2 = pkg.equals(getPackageName())
                        ? 0xFFA7F3D0
                        : 0xFFCBD5E1;
                    addRow(root, "·", shortName + "  [" + pkg + "]", color2);
                }
            }
        } catch (Throwable t) {
            addRow(root, "System lookup", "ERROR: " + t.getMessage(), 0xFFFCA5A5);
        }

        addSpacer(root, 12);

        // ==== LIVE LOG ==============================================
        addHeader(root, "LIVE LOG (last 30)", 0xFFFCD34D);
        addSpacer(root, 4);
        String logTail = ServiaWearLog.tail(this, 30);
        TextView logView = new TextView(this);
        logView.setText(logTail);
        logView.setTextColor(0xFFA7F3D0);
        logView.setTextSize(9);
        logView.setTypeface(Typeface.MONOSPACE);
        logView.setLayoutParams(wrap());
        root.addView(logView);

        addSpacer(root, 12);

        TextView footer = new TextView(this);
        try {
            android.content.pm.PackageInfo pi = getPackageManager().getPackageInfo(getPackageName(), 0);
            footer.setText("v" + pi.versionName + " · " + (Build.MANUFACTURER.toLowerCase().contains("samsung") ? "Samsung Wear OS" : "Wear OS"));
        } catch (Throwable t) {
            footer.setText("v? · " + Build.MANUFACTURER);
        }
        footer.setTextColor(0xFF64748B);
        footer.setTextSize(9);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer);
    }

    // ---- ACTIONS ------------------------------------------------------

    /**
     * Fire WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER for the
     * Burj Sunset face. The system's wallpaper-preview screen opens;
     * the user taps "Set wallpaper" / "Apply" there to actually install
     * the face. This is the official way a third-party app applies its
     * watch face on user devices.
     *
     * If the wallpaper preview activity rejects (some Samsung One UI
     * versions block it), fall back to opening the watch face
     * customizer carousel.
     */
    /**
     * v1.24.51 — try 5 different intents in sequence to apply
     * ServiaFace01BurjSunset. Whichever one Samsung's One UI Watch
     * actually accepts (if any) wins. Each attempt is logged so the
     * server's diag-recent endpoint shows us the result.
     */
    private void applyFace(String targetClass) {
        ComponentName cn = new ComponentName(this, targetClass);
        ServiaWearLog.log(this, "APPLY",
            "begin — target=" + cn.flattenToShortString());

        // Attempt 1: standard Live Wallpaper picker (with explicit component)
        if (tryStart("live-wallpaper", () -> {
            Intent i = new Intent(WallpaperManager.ACTION_CHANGE_LIVE_WALLPAPER);
            i.putExtra(WallpaperManager.EXTRA_LIVE_WALLPAPER_COMPONENT, cn);
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            return i;
        })) return;

        // Attempt 2: Google's hard-coded watch-face surface intent
        if (tryStart("google-set-watchface", () -> {
            Intent i = new Intent("com.google.android.wearable.app.cn.SET_WATCH_FACE");
            i.setComponent(cn);
            i.putExtra("watchface", cn.flattenToShortString());
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            return i;
        })) return;

        // Attempt 3: Samsung One UI watch-face manager
        if (tryStart("samsung-watch-manager", () -> {
            Intent i = new Intent("com.samsung.android.app.watchmanagerstub.action.WATCH_FACE");
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            i.putExtra("component", cn.flattenToShortString());
            return i;
        })) return;

        // Attempt 4: Samsung One UI Watch face picker
        if (tryStart("samsung-pick-watchface", () -> {
            Intent i = new Intent("com.samsung.android.wearable.watchface.action.OPEN_GALLERY");
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            return i;
        })) return;

        // Attempt 5: open the Wear OS system Settings → Wallpapers
        if (tryStart("system-wallpaper-settings", () -> {
            Intent i = new Intent("android.settings.WALLPAPER_SETTINGS");
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            return i;
        })) return;

        ServiaWearLog.log(this, "APPLY", "ALL 5 ATTEMPTS FAILED");
        Toast.makeText(this,
            "All 5 picker intents failed. Tap 'SEND LOG' so I can read why.",
            Toast.LENGTH_LONG).show();
    }

    /** Try to start the intent; log success/fail; return true if started. */
    private boolean tryStart(String label, java.util.function.Supplier<Intent> mk) {
        try {
            Intent i = mk.get();
            // Check if anything resolves before launching.
            if (i.resolveActivity(getPackageManager()) == null) {
                ServiaWearLog.log(this, "APPLY", label + " · no activity resolves");
                return false;
            }
            startActivity(i);
            ServiaWearLog.log(this, "APPLY", label + " · launched OK");
            Toast.makeText(this, "Tried: " + label, Toast.LENGTH_SHORT).show();
            return true;
        } catch (Throwable t) {
            ServiaWearLog.log(this, "APPLY",
                label + " · FAIL: " + (t.getMessage() == null ? t.getClass().getSimpleName() : t.getMessage()));
            return false;
        }
    }

    /** Send the diagnostic dump + log tail to /api/wear/diag-log. */
    private void sendLog() {
        sendStatusView.setText("Sending…");
        sendStatusView.setTextColor(0xFFFCD34D);
        bg.submit(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("device_id", Build.MODEL + "·" + Build.FINGERPRINT.hashCode());
                body.put("manufacturer", Build.MANUFACTURER);
                body.put("model", Build.MODEL);
                body.put("sdk", Build.VERSION.SDK_INT);
                body.put("release", Build.VERSION.RELEASE);
                body.put("fingerprint", Build.FINGERPRINT);
                body.put("package", getPackageName());
                body.put("app_version",
                    getPackageManager().getPackageInfo(getPackageName(), 0).versionName);
                // Faces declared vs visible
                int declared = 0;
                try {
                    android.content.pm.PackageInfo pi = getPackageManager().getPackageInfo(
                        getPackageName(), PackageManager.GET_SERVICES);
                    if (pi.services != null) {
                        for (ServiceInfo s : pi.services) {
                            if (s.permission != null && s.permission.contains("BIND_WALLPAPER")) declared++;
                        }
                    }
                } catch (Throwable ignored) {}
                body.put("faces_declared", declared);
                int visible = 0;
                StringBuilder visibleList = new StringBuilder();
                try {
                    Intent wfIntent = new Intent("android.service.wallpaper.WallpaperService");
                    wfIntent.addCategory("com.google.android.wearable.watchface.category.WATCH_FACE");
                    List<ResolveInfo> resolved = getPackageManager().queryIntentServices(wfIntent, 0);
                    visible = resolved == null ? 0 : resolved.size();
                    if (resolved != null) {
                        for (ResolveInfo ri : resolved) {
                            visibleList.append(ri.serviceInfo == null ? "?" : (ri.serviceInfo.packageName + "/" + ri.serviceInfo.name)).append("\n");
                        }
                    }
                } catch (Throwable ignored) {}
                body.put("faces_visible_to_system", visible);
                body.put("faces_visible_list", visibleList.toString());
                body.put("log_tail", ServiaWearLog.tail(this, 200));

                URL u = new URL("https://servia.ae/api/wear/diag-log");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("User-Agent", "ServiaWear/1.24.47 (Android Wear OS)");
                con.setConnectTimeout(8000);
                con.setReadTimeout(15000);
                con.setDoOutput(true);
                try (OutputStream os = con.getOutputStream()) {
                    os.write(body.toString().getBytes(StandardCharsets.UTF_8));
                }
                int code = con.getResponseCode();
                BufferedReader r = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(),
                    StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder();
                String line; while ((line = r.readLine()) != null) sb.append(line);
                r.close();
                final int fcode = code;
                final String fbody = sb.toString();
                ui.post(() -> {
                    if (fcode >= 200 && fcode < 300) {
                        sendStatusView.setText("✅ Sent (" + fcode + ")");
                        sendStatusView.setTextColor(0xFFA7F3D0);
                    } else {
                        sendStatusView.setText("⚠ HTTP " + fcode + ": " + clip(fbody, 60));
                        sendStatusView.setTextColor(0xFFFCA5A5);
                    }
                });
                ServiaWearLog.log(this, "SEND_LOG", "result HTTP " + fcode);
            } catch (Throwable t) {
                final String em = t.getMessage();
                ui.post(() -> {
                    sendStatusView.setText("⚠ " + (em == null ? "Network error" : em));
                    sendStatusView.setTextColor(0xFFFCA5A5);
                });
                ServiaWearLog.log(this, "SEND_LOG", "FAIL " + em);
            }
        });
    }

    // ---- helpers ------------------------------------------------------

    private void addActionButton(LinearLayout p, String text, int bg, int fg,
                                  View.OnClickListener click) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(fg);
        t.setBackgroundColor(bg);
        t.setTextSize(13);
        t.setGravity(Gravity.CENTER);
        t.setPadding(8, 16, 8, 16);
        t.setTypeface(t.getTypeface(), Typeface.BOLD);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = 6;
        t.setLayoutParams(lp);
        t.setClickable(true);
        t.setOnClickListener(click);
        p.addView(t);
    }

    private void addHeader(LinearLayout p, String text, int color) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(color);
        t.setTextSize(11);
        t.setLetterSpacing(0.20f);
        t.setTypeface(t.getTypeface(), Typeface.BOLD);
        t.setGravity(Gravity.CENTER);
        p.addView(t);
    }

    private void addBody(LinearLayout p, String text, int color) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(color);
        t.setTextSize(11);
        t.setGravity(Gravity.START);
        t.setLayoutParams(wrap());
        p.addView(t);
    }

    private void addRow(LinearLayout p, String key, String val, int valColor) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setLayoutParams(wrap());
        TextView k = new TextView(this);
        k.setText(key);
        k.setTextColor(0xFF94A3B8);
        k.setTextSize(10);
        LinearLayout.LayoutParams klp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        k.setLayoutParams(klp);
        row.addView(k);
        TextView v = new TextView(this);
        v.setText(val);
        v.setTextColor(valColor);
        v.setTextSize(10);
        v.setTypeface(Typeface.MONOSPACE);
        LinearLayout.LayoutParams vlp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 2);
        v.setLayoutParams(vlp);
        row.addView(v);
        p.addView(row);
    }

    private void addSpacer(LinearLayout p, int dp) {
        TextView t = new TextView(this);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, (int)(dp * getResources().getDisplayMetrics().density));
        t.setLayoutParams(lp);
        p.addView(t);
    }

    private LinearLayout.LayoutParams wrap() {
        return new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private String clip(String s, int n) {
        if (s == null) return "—";
        return s.length() <= n ? s : s.substring(0, n - 1) + "…";
    }
}
