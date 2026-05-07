package ae.servia.wear.watchface;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * v1.24.33 — slot-binding storage for the Servia watch face.
 *
 * Each preset exposes N slots (2..6). Each slot stores a "kind" — one of:
 *
 *   sos_1 .. sos_5     Custom SOS shortcut bound to QuadTile slot 1..5
 *                      (resolves to SharedPreferences "servia_csos_slots").
 *   talk               Open VoiceAssistantActivity.
 *   book               Open QuickBookActivity.
 *   track              Open BookingTrackActivity.
 *   address            Open LocationActivity.
 *   wallet             Future complication; for now opens Wallet placeholder.
 *   weather            Read-only complication, no tap action.
 *   battery            Read-only complication, no tap action.
 *   steps              Read-only complication, no tap action.
 *   next_booking       Read-only — booking ETA pushed by listener service.
 *   none               Empty.
 *
 * Persistence: SharedPreferences "servia_watch_face":
 *   active_preset_id  (string)
 *   slot_{n}_kind     (string)  — overrides preset default if present.
 */
public final class WatchFaceSlots {

    public static final String PREFS = "servia_watch_face";
    public static final String KEY_PRESET = "active_preset_id";

    public static final String[] KINDS = {
        "sos_1", "sos_2", "sos_3", "sos_4", "sos_5",
        "talk", "book", "track", "address", "nfc",
        "wallet", "weather", "battery", "steps", "next_booking",
        "none",
    };

    public static final String[] LABELS = {
        "🆘 SOS 1", "🆘 SOS 2", "🆘 SOS 3", "🆘 SOS 4", "🆘 SOS 5",
        "🎙 Talk", "📋 Book", "📍 Track", "🏠 Address", "📡 NFC",
        "👛 Wallet", "☁ Weather", "🔋 Battery", "👣 Steps", "📅 Next",
        "—",
    };

    public static String labelFor(String kind) {
        if (kind == null) return "—";
        for (int i = 0; i < KINDS.length; i++) {
            if (KINDS[i].equals(kind)) return LABELS[i];
        }
        return "—";
    }

    public static String activePresetId(Context ctx) {
        return ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                  .getString(KEY_PRESET, WatchFacePreset.ALL[0].id);
    }

    public static void setActivePresetId(Context ctx, String id) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit().putString(KEY_PRESET, id).apply();
    }

    /** Resolves slot kind: stored override → preset default. */
    public static String slotKind(Context ctx, WatchFacePreset preset, int slot) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String override = sp.getString("slot_" + slot + "_kind", null);
        if (override != null) return override;
        if (slot < preset.defaultSlots.length) return preset.defaultSlots[slot];
        return "none";
    }

    public static void setSlotKind(Context ctx, int slot, String kind) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit().putString("slot_" + slot + "_kind", kind).apply();
    }

    public static void clearSlotOverride(Context ctx, int slot) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit().remove("slot_" + slot + "_kind").apply();
    }

    /**
     * For tap dispatch — returns {activityClassName, extraSlotNumberOrNull}.
     * Returns null if the slot kind has no action (read-only complications).
     */
    public static String[] resolveTapAction(String kind) {
        if (kind == null) return null;
        if (kind.startsWith("sos_")) {
            // sos_N -> CustomSosSlotDispatchActivity with extra "slot"=N
            int n;
            try { n = Integer.parseInt(kind.substring(4)); }
            catch (Exception e) { return null; }
            return new String[]{"ae.servia.wear.CustomSosSlotDispatchActivity",
                                String.valueOf(n)};
        }
        switch (kind) {
            case "talk":    return new String[]{"ae.servia.wear.VoiceAssistantActivity", null};
            case "book":    return new String[]{"ae.servia.wear.QuickBookActivity", null};
            case "track":   return new String[]{"ae.servia.wear.BookingTrackActivity", null};
            case "address": return new String[]{"ae.servia.wear.LocationActivity", null};
            case "nfc":     return new String[]{"ae.servia.wear.NfcScanActivity", null};
        }
        return null;
    }
}
