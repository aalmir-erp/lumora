package ae.servia.wfpusher;

import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.os.Build;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Method;

/**
 * v1.24.54 — Watch Face Push API driver (Plan A).
 *
 * Flow:
 *   1. On first run, request com.google.wear.permission.PUSH_WATCH_FACES.
 *   2. Extract assets/burjsunset.apk to internal storage so we have a
 *      File handle (the Push API takes a ParcelFileDescriptor).
 *   3. Open it as a ParcelFileDescriptor, call addWatchFace().
 *   4. Take the returned slot id, call setWatchFaceAsActive(slotId).
 *   5. The on-watch runtime now switches the live face to ours,
 *      bypassing the Samsung One UI Watch picker filter entirely.
 *
 * Reflection notes: androidx.wear.watchface:watchface-push:1.3+ is a
 * recent artifact. To keep this APK installable on watches without
 * the runtime artifact present (graceful failure), every call into
 * WatchFacePushManager goes through reflection. If the class isn't
 * present we surface a clean error in the UI instead of crashing.
 *
 * Validation token: WFF Push payloads normally require a Google-issued
 * validation token to install. On a developer-mode watch (which the
 * user has — DEVELOPER_OPTIONS_ENABLED=1 from the diagnostic dump),
 * an empty token is accepted. We pass "" first; if the runtime
 * rejects it, the status field will say so and we surface the
 * actual error message to the user.
 */
public class PushActivity extends Activity {

    private static final String FACE_ASSET = "burjsunset.apk";
    private static final String FACE_PKG   = "ae.servia.wff.burjsunset";
    private static final int    REQ_PUSH_PERM = 4242;

    private TextView statusTv;
    private TextView versionTv;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        int layout = getResources().getIdentifier(
            "activity_push", "layout", getPackageName());
        setContentView(layout);

        statusTv  = findViewById(idOf("status"));
        versionTv = findViewById(idOf("version"));
        try {
            String v = getPackageManager()
                .getPackageInfo(getPackageName(), 0).versionName;
            versionTv.setText("v" + v + " · sdk " + Build.VERSION.SDK_INT);
        } catch (Throwable ignored) {
            versionTv.setText("v?");
        }

        Button push   = findViewById(idOf("btn_push"));
        Button list   = findViewById(idOf("btn_list"));
        Button remove = findViewById(idOf("btn_remove"));
        push.setOnClickListener(v -> doPush());
        list.setOnClickListener(v -> doList());
        remove.setOnClickListener(v -> doRemove());
    }

    private int idOf(String name) {
        return getResources().getIdentifier(name, "id", getPackageName());
    }

    /* ------------------------------------------------------------------ */

    private void setStatus(String s) {
        runOnUiThread(() -> statusTv.setText(s));
    }
    private void appendStatus(String s) {
        runOnUiThread(() -> statusTv.setText(statusTv.getText() + "\n" + s));
    }

    private boolean ensurePermission() {
        String perm = "com.google.wear.permission.PUSH_WATCH_FACES";
        if (checkSelfPermission(perm) == PackageManager.PERMISSION_GRANTED) return true;
        requestPermissions(new String[]{ perm }, REQ_PUSH_PERM);
        return false;
    }

    @Override
    public void onRequestPermissionsResult(int reqCode, String[] perms, int[] results) {
        super.onRequestPermissionsResult(reqCode, perms, results);
        if (reqCode == REQ_PUSH_PERM) {
            if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
                appendStatus("permission GRANTED — tap Push & Activate again");
            } else {
                appendStatus("permission DENIED — settings → app permissions to grant");
            }
        }
    }

    /* ------------------------------------------------------------------ */

    private void doPush() {
        setStatus("PUSH: starting...");
        if (!ensurePermission()) {
            appendStatus("PUSH: requesting permission, will retry after grant");
            return;
        }
        new AsyncTask<Void, String, String>() {
            @Override protected String doInBackground(Void... args) {
                try {
                    publishProgress("PUSH: extracting payload");
                    File payload = extractAsset();
                    publishProgress("PUSH: payload size = " + payload.length() + " bytes");

                    publishProgress("PUSH: getting WatchFacePushManager");
                    Object mgr = getManager();
                    if (mgr == null) {
                        return "ERR: WatchFacePushManager not available — "
                             + "watchface-push artifact missing or runtime "
                             + "not installed on this device";
                    }

                    publishProgress("PUSH: opening PFD");
                    ParcelFileDescriptor pfd = ParcelFileDescriptor.open(
                        payload, ParcelFileDescriptor.MODE_READ_ONLY);

                    publishProgress("PUSH: calling addWatchFace(token=\"\")");
                    Object result = invokeAddWatchFace(mgr, pfd, "");
                    publishProgress("PUSH: addWatchFace returned " + result);

                    String slotId = extractSlotId(result);
                    if (slotId == null) slotId = FACE_PKG;
                    publishProgress("PUSH: slotId = " + slotId);

                    publishProgress("PUSH: calling setWatchFaceAsActive(" + slotId + ")");
                    Object setResult = invokeSetActive(mgr, slotId);
                    publishProgress("PUSH: setActive returned " + setResult);

                    return "✅ DONE — face pushed and activated.\nIf the watch face didn't change, open Customize Watch Faces.";
                } catch (Throwable t) {
                    return "ERR: " + t.getClass().getSimpleName() + ": " + t.getMessage();
                }
            }
            @Override protected void onProgressUpdate(String... values) {
                for (String v : values) appendStatus(v);
            }
            @Override protected void onPostExecute(String s) { appendStatus(s); }
        }.execute();
    }

    private void doList() {
        setStatus("LIST: starting...");
        if (!ensurePermission()) return;
        new AsyncTask<Void, String, String>() {
            @Override protected String doInBackground(Void... args) {
                try {
                    Object mgr = getManager();
                    if (mgr == null) return "ERR: WatchFacePushManager not available";

                    Object listFuture = mgr.getClass().getMethod("listWatchFaces").invoke(mgr);
                    Object response = waitFuture(listFuture, 10);
                    return "LIST: " + (response == null ? "null" : response.toString());
                } catch (Throwable t) {
                    return "ERR: " + t.getClass().getSimpleName() + ": " + t.getMessage();
                }
            }
            @Override protected void onPostExecute(String s) { appendStatus(s); }
        }.execute();
    }

    private void doRemove() {
        setStatus("REMOVE: starting...");
        if (!ensurePermission()) return;
        new AsyncTask<Void, String, String>() {
            @Override protected String doInBackground(Void... args) {
                try {
                    Object mgr = getManager();
                    if (mgr == null) return "ERR: WatchFacePushManager not available";
                    Method remove = mgr.getClass().getMethod("removeWatchFace", String.class);
                    Object f = remove.invoke(mgr, FACE_PKG);
                    waitFuture(f, 10);
                    return "REMOVE: ok (" + FACE_PKG + ")";
                } catch (Throwable t) {
                    return "ERR: " + t.getClass().getSimpleName() + ": " + t.getMessage();
                }
            }
            @Override protected void onPostExecute(String s) { appendStatus(s); }
        }.execute();
    }

    /* ----------------- Reflection helpers ----------------------------- */

    private Object getManager() throws Exception {
        Class<?> factory = Class.forName(
            "androidx.wear.watchface.push.WatchFacePushManagerFactory");
        Method create = factory.getMethod(
            "createWatchFacePushManager", android.content.Context.class);
        return create.invoke(null, this);
    }

    private Object invokeAddWatchFace(Object mgr, ParcelFileDescriptor pfd, String token) throws Exception {
        // androidx.wear.watchface.push.WatchFacePushManager#addWatchFace
        // Signature in 1.3+: addWatchFace(ParcelFileDescriptor, String)
        // Returns ListenableFuture<...>.
        Method add = null;
        for (Method m : mgr.getClass().getMethods()) {
            if (m.getName().equals("addWatchFace") && m.getParameterCount() == 2) {
                add = m;
                break;
            }
        }
        if (add == null) throw new NoSuchMethodException("addWatchFace(PFD,String) not found");
        Object future = add.invoke(mgr, pfd, token);
        return waitFuture(future, 30);
    }

    private Object invokeSetActive(Object mgr, String slotId) throws Exception {
        Method m = null;
        for (Method candidate : mgr.getClass().getMethods()) {
            String n = candidate.getName();
            if ((n.equals("setWatchFaceAsActive") || n.equals("setActiveWatchFace"))
                && candidate.getParameterCount() == 1) {
                m = candidate;
                break;
            }
        }
        if (m == null) throw new NoSuchMethodException("setWatchFaceAsActive/setActiveWatchFace not found");
        Object future = m.invoke(mgr, slotId);
        return waitFuture(future, 10);
    }

    private String extractSlotId(Object response) {
        if (response == null) return null;
        // Try .getSlotId(), .getPackageName(), .getId() in order
        for (String getter : new String[]{ "getSlotId", "getPackageName", "getId" }) {
            try {
                Method m = response.getClass().getMethod(getter);
                Object v = m.invoke(response);
                if (v instanceof String) return (String) v;
            } catch (Throwable ignored) {}
        }
        return null;
    }

    private Object waitFuture(Object future, int seconds) throws Exception {
        if (future == null) return null;
        Method get = null;
        try {
            get = future.getClass().getMethod("get",
                long.class, java.util.concurrent.TimeUnit.class);
        } catch (NoSuchMethodException nse) {
            // Fallback: Future.get()
            try {
                get = future.getClass().getMethod("get");
                return get.invoke(future);
            } catch (Throwable t2) {
                return future;
            }
        }
        return get.invoke(future, (long) seconds, java.util.concurrent.TimeUnit.SECONDS);
    }

    private File extractAsset() throws Exception {
        File out = new File(getCacheDir(), FACE_ASSET);
        if (out.exists()) out.delete();
        try (InputStream in = getAssets().open(FACE_ASSET);
             OutputStream os = new FileOutputStream(out)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) os.write(buf, 0, n);
        }
        return out;
    }
}
