package ae.servia.wear.faces;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.pm.ServiceInfo;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.List;

/**
 * v1.24.43 — Servia Faces standalone-APK launcher with BUILT-IN
 * DIAGNOSTICS so the user can see exactly why faces aren't appearing
 * in the system picker.
 *
 * Shows:
 *   - Build version + applicationId + targetSdk
 *   - Wear OS version
 *   - Watch model
 *   - How many watch face services this APK declares
 *   - How many watch face services the OS sees system-wide
 *   - Whether the wallpaper service intent resolves
 *   - Errors (red text) for anything that's broken
 */
public class LauncherActivity extends Activity {
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
        addSpacer(root, 6);

        // Activation hint
        addBody(root, "To activate:\n1. Long-press watch face\n2. Customize watch faces\n3. Pick any 'Servia · …'\n", 0xFFFFFFFF);
        addSpacer(root, 10);

        // ==== DIAGNOSTICS ====
        addHeader(root, "DIAGNOSTICS", 0xFFFCD34D);
        addSpacer(root, 4);

        // Build info
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

        // Count watch face services in THIS package
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

        // Count watch face services SYSTEM-WIDE
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
                        ? 0xFFA7F3D0   // ours — green
                        : 0xFFCBD5E1;   // others — gray
                    addRow(root, "·", shortName + "  [" + pkg + "]", color2);
                }
            }
        } catch (Throwable t) {
            addRow(root, "System lookup", "ERROR: " + t.getMessage(), 0xFFFCA5A5);
        }

        addSpacer(root, 8);
        addBody(root,
            "If 'Faces visible to system' is 0 but 'Faces declared' > 0, the manifest registration is correct but Wear OS isn't enumerating us. Common cause: directBootAware missing or wallpaper descriptor xml not bundled.",
            0xFF94A3B8);
        addSpacer(root, 14);

        // ==== LIVE LOG ====
        addHeader(root, "LIVE LOG (last 30)", 0xFFFCD34D);
        addSpacer(root, 4);
        String logTail = ae.servia.wear.watchface.ServiaWearLog.tail(this, 30);
        TextView logView = new TextView(this);
        logView.setText(logTail);
        logView.setTextColor(0xFFA7F3D0);
        logView.setTextSize(9);
        logView.setTypeface(Typeface.MONOSPACE);
        logView.setLayoutParams(wrap());
        root.addView(logView);

        addSpacer(root, 12);

        TextView footer = new TextView(this);
        footer.setText("v1.24.45 · " + (Build.MANUFACTURER.toLowerCase().contains("samsung") ? "Samsung Wear OS" : "Wear OS"));
        footer.setTextColor(0xFF64748B);
        footer.setTextSize(9);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer);
    }

    // ---- helpers ------------------------------------------------------

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
