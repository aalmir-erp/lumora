package ae.servia.pusher;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * v1.24.54 — Servia Watch Face Pusher activity.
 *
 * On Push:
 *   1. Copies the bundled wff-only payload APK out of /res/raw/ into the
 *      app's cacheDir (the Push API expects a real File).
 *   2. Reflectively constructs WatchFacePushManager from
 *      androidx.wear.watchface.push.WatchFacePushManagerFactory.
 *   3. Calls addWatchFace(File, String token) and routes the resulting
 *      ListenableFuture's status to the on-screen TextView.
 *   4. On success, optionally calls setActiveWatchFace(slotId) so the
 *      face is showing immediately when the user looks at the watch.
 *
 * Reflection over a direct API call is intentional: the Push API is
 * still in alpha (1.0.0-alpha02 as of Jan 2026), the package layout
 * has been changing release-to-release, and we want a build that
 * compiles even if the artifact is briefly unresolvable. Failures
 * surface as runtime errors in the on-screen log, where Bugjaeger can
 * read them off the device.
 */
public class PusherActivity extends Activity {

    private static final String TAG = "ServiaPusher";
    private static final String PAYLOAD_TOKEN = "servia-burj-sunset-v1.24.54";

    private TextView log;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_pusher);

        log = findViewById(R.id.log);
        Button pushBtn = findViewById(R.id.btn_push);
        Button listBtn = findViewById(R.id.btn_list);

        appendLog("Servia Pusher v1.24.54");
        appendLog("App: ae.servia.pusher");
        appendLog("Payload: ae.servia.wff.burjsunset");
        appendLog("");
        appendLog("Tap PUSH to install Burj Sunset.");
        appendLog("Tap LIST to see slots already pushed.");

        pushBtn.setOnClickListener(v -> doPush());
        listBtn.setOnClickListener(v -> doList());
    }

    private void doPush() {
        appendLog("--- PUSH ---");
        try {
            File apk = extractPayload();
            appendLog("Extracted payload: " + apk.getAbsolutePath() +
                    " (" + apk.length() + " bytes)");

            Object manager = createPushManager();
            if (manager == null) {
                appendLog("ERROR: WatchFacePushManager not available on this device.");
                appendLog("Requires Wear OS 5.1+ with Push API support.");
                return;
            }

            // Reflectively invoke addWatchFace(File, String).
            Object future = manager.getClass()
                    .getMethod("addWatchFace", File.class, String.class)
                    .invoke(manager, apk, PAYLOAD_TOKEN);
            appendLog("addWatchFace() returned: " + future);

            // Most Push API result types are ListenableFuture<Slot>.
            // Block briefly on .get() — the call is fast on success.
            Object slot = future.getClass().getMethod("get").invoke(future);
            appendLog("Slot: " + slot);
            appendLog("PUSH OK — face should now be selectable.");

            // Try to make it active. Method name varies by alpha — we
            // try setWatchFaceAsActive first, fall back to setActiveSlot.
            String slotId = String.valueOf(
                    slot.getClass().getMethod("getSlotId").invoke(slot));
            appendLog("Slot ID: " + slotId);

            try {
                manager.getClass()
                        .getMethod("setWatchFaceAsActive", String.class)
                        .invoke(manager, slotId);
                appendLog("Set active OK.");
            } catch (NoSuchMethodException e) {
                appendLog("setWatchFaceAsActive not present, skipping.");
            }
        } catch (Throwable t) {
            Log.e(TAG, "push failed", t);
            appendLog("EXCEPTION: " + t.getClass().getSimpleName() +
                    ": " + t.getMessage());
            Throwable cause = t.getCause();
            if (cause != null) {
                appendLog("  caused by: " + cause.getClass().getSimpleName() +
                        ": " + cause.getMessage());
            }
        }
    }

    private void doList() {
        appendLog("--- LIST ---");
        try {
            Object manager = createPushManager();
            if (manager == null) {
                appendLog("ERROR: WatchFacePushManager not available.");
                return;
            }
            Object future = manager.getClass()
                    .getMethod("listWatchFaces")
                    .invoke(manager);
            Object result = future.getClass().getMethod("get").invoke(future);
            appendLog("Slots: " + result);
        } catch (Throwable t) {
            Log.e(TAG, "list failed", t);
            appendLog("EXCEPTION: " + t.getClass().getSimpleName() +
                    ": " + t.getMessage());
        }
    }

    /**
     * Reflectively create a WatchFacePushManager. Tries the documented
     * factory class first, falls back to a direct constructor on the
     * Manager class itself (alpha API surface differs across releases).
     */
    private Object createPushManager() throws Exception {
        // Preferred: WatchFacePushManagerFactory.create(Context).
        try {
            Class<?> factory = Class.forName(
                    "androidx.wear.watchface.push.WatchFacePushManagerFactory");
            return factory.getMethod("create", android.content.Context.class)
                    .invoke(null, this);
        } catch (ClassNotFoundException ignored) {
            // fall through
        }
        // Fallback: WatchFacePushManager(Context) ctor.
        try {
            Class<?> mgr = Class.forName(
                    "androidx.wear.watchface.push.WatchFacePushManager");
            return mgr.getConstructor(android.content.Context.class)
                    .newInstance(this);
        } catch (ClassNotFoundException ignored) {
            return null;
        }
    }

    /** Copy res/raw/payload.apk into cacheDir for hand-off to the API. */
    private File extractPayload() throws Exception {
        File out = new File(getCacheDir(), "burj-sunset-payload.apk");
        if (out.exists()) out.delete();
        try (InputStream in = getResources().openRawResource(R.raw.payload);
             OutputStream os = new FileOutputStream(out)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) > 0) os.write(buf, 0, n);
        }
        return out;
    }

    private void appendLog(String line) {
        Log.i(TAG, line);
        if (log != null) {
            log.append(line + "\n");
        }
    }
}
