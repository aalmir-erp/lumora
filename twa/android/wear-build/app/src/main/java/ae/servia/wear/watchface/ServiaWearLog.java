package ae.servia.wear.watchface;

import android.content.Context;
import android.os.Build;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * v1.24.45 — append-only file log so the customer can read exactly what
 * happened on the watch without ADB. Writes to
 *   <ExternalFilesDir>/logs/servia-wear.log
 *
 * Read from the LauncherActivity (which tails this file and shows the
 * last 30 lines).
 *
 * Every line is prefixed with HH:MM:SS so we can correlate with the
 * customer's actions ("at 14:30 I tapped the picker — log shows X").
 */
public final class ServiaWearLog {
    private static final String TAG = "ServiaWear";
    private static final String FILENAME = "servia-wear.log";

    private ServiaWearLog() {}

    public static synchronized void log(Context ctx, String tag, String msg) {
        Log.i(TAG, tag + " · " + msg);
        try {
            File dir = new File(ctx.getExternalFilesDir(null), "logs");
            if (!dir.exists()) dir.mkdirs();
            File f = new File(dir, FILENAME);
            // Cap at ~50KB rolling (truncate to last 30KB if larger)
            if (f.exists() && f.length() > 50 * 1024) {
                truncate(f);
            }
            FileOutputStream fos = new FileOutputStream(f, true);
            try (OutputStreamWriter w = new OutputStreamWriter(fos, "UTF-8")) {
                String ts = new SimpleDateFormat("HH:mm:ss", Locale.US).format(new Date());
                w.write(ts + " " + tag + ": " + msg + "\n");
            }
        } catch (Throwable t) {
            Log.w(TAG, "log write failed: " + t.getMessage());
        }
    }

    public static synchronized String tail(Context ctx, int maxLines) {
        try {
            File f = new File(new File(ctx.getExternalFilesDir(null), "logs"), FILENAME);
            if (!f.exists()) return "(no log yet)";
            // Read whole file (capped at 50KB so OK)
            java.io.FileInputStream fis = new java.io.FileInputStream(f);
            byte[] buf = new byte[(int) f.length()];
            fis.read(buf); fis.close();
            String all = new String(buf, "UTF-8");
            String[] lines = all.split("\n");
            int start = Math.max(0, lines.length - maxLines);
            StringBuilder sb = new StringBuilder();
            for (int i = start; i < lines.length; i++) {
                if (lines[i].isEmpty()) continue;
                sb.append(lines[i]).append('\n');
            }
            return sb.length() == 0 ? "(empty)" : sb.toString();
        } catch (Throwable t) {
            return "(log read failed: " + t.getMessage() + ")";
        }
    }

    private static void truncate(File f) {
        try {
            byte[] all = new byte[(int) f.length()];
            java.io.FileInputStream fis = new java.io.FileInputStream(f);
            fis.read(all); fis.close();
            // Keep last 30KB
            int cut = Math.max(0, all.length - 30 * 1024);
            byte[] tail = new byte[all.length - cut];
            System.arraycopy(all, cut, tail, 0, tail.length);
            FileOutputStream fos = new FileOutputStream(f, false);
            fos.write(tail); fos.close();
        } catch (Throwable ignored) {}
    }

    /** Convenience: log the device + build context once on app start. */
    public static void logBootInfo(Context ctx, String component) {
        try {
            String pkg = ctx.getPackageName();
            android.content.pm.PackageInfo pi = ctx.getPackageManager().getPackageInfo(pkg, 0);
            log(ctx, "BOOT", component + " · " + pkg + " v" + pi.versionName
                + " · SDK " + Build.VERSION.SDK_INT
                + " · " + Build.MANUFACTURER + " " + Build.MODEL);
        } catch (Throwable t) {
            log(ctx, "BOOT", component + " · pkg-info-failed: " + t.getMessage());
        }
    }
}
