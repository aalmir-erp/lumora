package ae.servia.pusher

import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.util.Log
import android.widget.Button
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import androidx.wear.watchfacepush.WatchFacePushManager
import androidx.wear.watchfacepush.WatchFacePushManagerFactory
import kotlinx.coroutines.launch
import java.io.File
import java.io.FileOutputStream

/**
 * v1.24.54 — Servia Watch Face Pusher activity.
 *
 * Push API surface (verbatim from the public release page, Jan 2026):
 *
 *   val mgr = WatchFacePushManagerFactory.createWatchFacePushManager(ctx)
 *   suspend fun addWatchFace(ParcelFileDescriptor, String): WatchFaceSlot
 *   suspend fun listWatchFaces(): WatchFaceSlotList
 *   suspend fun setWatchFaceAsActive(slotId: String)   // once-per-app-lifecycle
 *
 * Flow on PUSH:
 *   1. Extract the bundled wff-only APK (R.raw.payload) into cacheDir
 *      so we can open a ParcelFileDescriptor on a real File.
 *   2. addWatchFace(pfd, token) — token is a stable string; identical
 *      tokens replace the existing slot rather than allocating a new one.
 *   3. Mirror logcat to the on-screen TextView so Bugjaeger can read
 *      the result without an adb shell session.
 *   4. setWatchFaceAsActive(slot.slotId). May throw on second tap —
 *      that's a once-per-lifecycle limit, not a bug.
 */
class PusherActivity : ComponentActivity() {

    private companion object {
        const val TAG = "ServiaPusher"
        const val PAYLOAD_TOKEN = "servia-burj-sunset-v1-24-54"
    }

    private lateinit var logView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_pusher)

        logView = findViewById(R.id.log)
        findViewById<Button>(R.id.btn_push).setOnClickListener { doPush() }
        findViewById<Button>(R.id.btn_list).setOnClickListener { doList() }

        log("Servia Pusher v1.24.54")
        log("App: ae.servia.pusher")
        log("Payload: ae.servia.wff.burjsunset")
        log("")
        log("Tap PUSH to install Burj Sunset.")
        log("Tap LIST to enumerate slots.")
    }

    private fun doPush() = lifecycleScope.launch {
        log("--- PUSH ---")
        try {
            val apk = extractPayload()
            log("Extracted ${apk.length()} bytes -> ${apk.absolutePath}")
            val mgr = WatchFacePushManagerFactory.createWatchFacePushManager(this@PusherActivity)
            ParcelFileDescriptor.open(apk, ParcelFileDescriptor.MODE_READ_ONLY).use { pfd ->
                val slot = mgr.addWatchFace(pfd, PAYLOAD_TOKEN)
                log("addWatchFace OK")
                log("  slotId      = ${slot.slotId}")
                log("  packageName = ${slot.packageName}")
                log("  versionCode = ${slot.versionCode}")
                runCatching {
                    mgr.setWatchFaceAsActive(slot.slotId)
                    log("setWatchFaceAsActive OK — Burj Sunset is live.")
                }.onFailure {
                    log("setWatchFaceAsActive failed: ${it::class.simpleName}: ${it.message}")
                    log("(This is once-per-app-lifecycle. Reinstall the pusher to retry.)")
                }
            }
        } catch (t: Throwable) {
            Log.e(TAG, "push failed", t)
            log("EXCEPTION ${t::class.simpleName}: ${t.message}")
            t.cause?.let { log("  caused by ${it::class.simpleName}: ${it.message}") }
        }
    }

    private fun doList() = lifecycleScope.launch {
        log("--- LIST ---")
        try {
            val mgr = WatchFacePushManagerFactory.createWatchFacePushManager(this@PusherActivity)
            val resp = mgr.listWatchFaces()
            log("Slots free: ${resp.remainingSlotCount}")
            if (resp.installedWatchFaceDetails.isEmpty()) {
                log("No slots used by this app yet.")
            } else {
                resp.installedWatchFaceDetails.forEachIndexed { i, slot ->
                    log("[$i] ${slot.slotId}  ${slot.packageName} v${slot.versionCode}")
                }
            }
        } catch (t: Throwable) {
            Log.e(TAG, "list failed", t)
            log("EXCEPTION ${t::class.simpleName}: ${t.message}")
        }
    }

    private fun extractPayload(): File {
        val out = File(cacheDir, "burj-sunset-payload.apk")
        if (out.exists()) out.delete()
        resources.openRawResource(R.raw.payload).use { input ->
            FileOutputStream(out).use { output -> input.copyTo(output) }
        }
        return out
    }

    private fun log(line: String) {
        Log.i(TAG, line)
        runOnUiThread { logView.append("$line\n") }
    }
}
