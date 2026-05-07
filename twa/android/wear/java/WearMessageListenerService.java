package ae.servia.wear;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.util.Log;

import androidx.core.app.NotificationCompat;
import androidx.wear.tiles.TileService;

import com.google.android.gms.wearable.MessageEvent;
import com.google.android.gms.wearable.WearableListenerService;

import org.json.JSONObject;

/**
 * v1.24.30 — Phone → Watch Data Layer bridge.
 *
 * The companion phone app (or in lieu of one, the future TWA Wearable
 * bridge) publishes messages to these paths and the watch reacts:
 *
 *   /servia/booking_created   { booking_id, service, eta_min, vendor }
 *       → notification on the watch ("📋 Booking confirmed · 25m ETA")
 *         + tile refresh for NextBookingTileService.
 *
 *   /servia/sos_slot_bind     { slot, id, label, emoji }
 *       → write SharedPreferences ("servia_csos_slots") so the
 *         CustomSosSlot{n} + Quad tiles update next refresh.
 *
 *   /servia/sos_slot_clear    { slot }
 *       → remove a binding.
 *
 *   /servia/booking_update    { booking_id, status }     (existing)
 *   /servia/wallet_update     { balance_aed }            (existing)
 *   /servia/loyalty_update    { tier, points }           (existing)
 *
 * Tile refresh is requested via TileService.getUpdater(this).requestUpdate(...)
 * so the user doesn't have to swipe back and forth.
 */
public class WearMessageListenerService extends WearableListenerService {

    private static final String TAG = "ServiaWear";
    private static final String CHANNEL_BOOKING = "servia_bookings";

    @Override
    public void onMessageReceived(MessageEvent ev) {
        String path = ev.getPath();
        Log.i(TAG, "msg path=" + path + " from=" + ev.getSourceNodeId());

        try {
            JSONObject body = parsePayload(ev);
            switch (path == null ? "" : path) {
                case "/servia/booking_created":
                    handleBookingCreated(body);
                    break;
                case "/servia/sos_slot_bind":
                    handleSosSlotBind(body);
                    break;
                case "/servia/sos_slot_clear":
                    handleSosSlotClear(body);
                    break;
                default:
                    super.onMessageReceived(ev);
                    return;
            }
        } catch (Exception e) {
            Log.w(TAG, "msg handler failed", e);
        }
    }

    private JSONObject parsePayload(MessageEvent ev) {
        try {
            byte[] raw = ev.getData();
            if (raw == null || raw.length == 0) return new JSONObject();
            return new JSONObject(new String(raw, "UTF-8"));
        } catch (Exception e) {
            return new JSONObject();
        }
    }

    // ---------- booking_created ----------------------------------------

    private void handleBookingCreated(JSONObject body) {
        String bookingId = body.optString("booking_id", "");
        String service = body.optString("service", "Servia");
        int etaMin = body.optInt("eta_min", 0);
        String vendor = body.optString("vendor", "");

        // v1.24.35 — cache for the watch face's next_booking slot to render.
        getSharedPreferences("servia_next_booking", MODE_PRIVATE).edit()
            .putString("booking_id", bookingId)
            .putString("service", service)
            .putInt("eta_min", etaMin)
            .putString("vendor", vendor)
            .putLong("ts", System.currentTimeMillis())
            .apply();
        try {
            androidx.wear.tiles.TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.NextBookingTileService.class);
        } catch (Throwable ignored) {}

        ensureBookingChannel();

        Intent open = new Intent(this, BookingTrackActivity.class);
        open.putExtra("booking_id", bookingId);
        open.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        int reqCode = bookingId.hashCode();
        PendingIntent pi = PendingIntent.getActivity(this, reqCode, open,
            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);

        StringBuilder sb = new StringBuilder("✅ ").append(service);
        if (etaMin > 0) sb.append("  ·  ").append(etaMin).append("m ETA");
        if (!vendor.isEmpty()) sb.append("\n").append(vendor);

        Notification n = new NotificationCompat.Builder(this, CHANNEL_BOOKING)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Booking confirmed")
            .setContentText(sb.toString())
            .setStyle(new NotificationCompat.BigTextStyle().bigText(sb.toString()))
            .setContentIntent(pi)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setVibrate(new long[]{0, 200, 100, 200})
            .build();

        NotificationManager nm = (NotificationManager)
            getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null && !bookingId.isEmpty()) {
            nm.notify(reqCode, n);
        }

        // Refresh NextBooking tile so the new booking is glanceable.
        try {
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.NextBookingTileService.class);
        } catch (Throwable ignored) {}
    }

    private void ensureBookingChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager nm = (NotificationManager)
            getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null) return;
        if (nm.getNotificationChannel(CHANNEL_BOOKING) != null) return;
        NotificationChannel ch = new NotificationChannel(
            CHANNEL_BOOKING,
            "Booking updates",
            NotificationManager.IMPORTANCE_HIGH);
        ch.setDescription("Servia booking confirmations + ETA changes");
        ch.enableVibration(true);
        nm.createNotificationChannel(ch);
    }

    // ---------- sos_slot_bind / clear ----------------------------------

    private void handleSosSlotBind(JSONObject body) {
        int slot = body.optInt("slot", 0);
        if (slot < 1 || slot > 5) return;
        SharedPreferences sp = getSharedPreferences(
            "servia_csos_slots", MODE_PRIVATE);
        sp.edit()
          .putInt("csos_slot_" + slot + "_id", body.optInt("id"))
          .putString("csos_slot_" + slot + "_label", body.optString("label"))
          .putString("csos_slot_" + slot + "_emoji", body.optString("emoji", "🆘"))
          .apply();
        refreshSosTiles();
    }

    private void handleSosSlotClear(JSONObject body) {
        int slot = body.optInt("slot", 0);
        if (slot < 1 || slot > 5) return;
        SharedPreferences sp = getSharedPreferences(
            "servia_csos_slots", MODE_PRIVATE);
        sp.edit()
          .remove("csos_slot_" + slot + "_id")
          .remove("csos_slot_" + slot + "_label")
          .remove("csos_slot_" + slot + "_emoji")
          .apply();
        refreshSosTiles();
    }

    private void refreshSosTiles() {
        try {
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosQuadTileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosSlot1TileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosSlot2TileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosSlot3TileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosSlot4TileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosSlot5TileService.class);
        } catch (Throwable ignored) {}
    }
}
