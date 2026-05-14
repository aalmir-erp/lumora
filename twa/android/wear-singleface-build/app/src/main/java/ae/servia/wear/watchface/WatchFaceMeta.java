package ae.servia.wear.watchface;

import android.content.Context;
import android.graphics.Typeface;

import java.util.HashMap;
import java.util.Map;

/**
 * v1.24.43 — per-face metadata table.
 *
 * Each entry tells the renderer where + how to paint the live time on
 * top of the face's static frame bitmap. Generated from the SVG sources
 * in tools/watchface/generate.py — keep in sync if you re-design.
 *
 * Resource references are stored as STRINGS not int IDs so the same
 * compiled bytecode runs in both the main Servia Wear APK
 * (namespace ae.servia.wear) and the standalone Servia Faces APK
 * (namespace ae.servia.wear.faces). Renderer resolves to int via
 * Resources.getIdentifier() at runtime.
 *
 * Time position (timeX, timeY) is the SVG anchor on a 480 grid. Renderer
 * scales to actual surface width.
 */
public final class WatchFaceMeta {

    public static final class Entry {
        public final String id;
        public final String name;
        public final String frameResName;    // e.g. "wf_frame_p01"
        public final String previewResName;  // e.g. "wf_preview_p01"
        public final float timeX;            // 480-grid; renderer scales
        public final float timeY;
        public final int timeSize;
        public final int timeColor;          // 0xAARRGGBB
        public final int timeWeight;
        public final float timeLetterSpacing;
        public final boolean timeSerif;
        public final boolean timeMonospace;
        public final boolean hasSecondHand;

        public Entry(String id, String name,
                     String frameResName, String previewResName,
                     float timeX, float timeY, int timeSize, int timeColor,
                     int timeWeight, float timeLetterSpacing,
                     boolean timeSerif, boolean timeMonospace,
                     boolean hasSecondHand) {
            this.id = id; this.name = name;
            this.frameResName = frameResName;
            this.previewResName = previewResName;
            this.timeX = timeX; this.timeY = timeY;
            this.timeSize = timeSize; this.timeColor = timeColor;
            this.timeWeight = timeWeight;
            this.timeLetterSpacing = timeLetterSpacing;
            this.timeSerif = timeSerif; this.timeMonospace = timeMonospace;
            this.hasSecondHand = hasSecondHand;
        }
        public Typeface typeface() {
            if (timeMonospace) return Typeface.MONOSPACE;
            if (timeSerif) return Typeface.SERIF;
            return Typeface.SANS_SERIF;
        }
        public int typefaceStyle() {
            return timeWeight >= 700 ? Typeface.BOLD : Typeface.NORMAL;
        }
        /** Resolve drawable resource id at runtime (package-agnostic). */
        public int resolveFrameRes(Context ctx) {
            return ctx.getResources().getIdentifier(
                frameResName, "drawable", ctx.getPackageName());
        }
        public int resolvePreviewRes(Context ctx) {
            return ctx.getResources().getIdentifier(
                previewResName, "drawable", ctx.getPackageName());
        }
    }

    private static final Map<String, Entry> BY_ID = new HashMap<>();

    static void put(Entry e) { BY_ID.put(e.id, e); }
    public static Entry byId(String id) {
        Entry e = BY_ID.get(id);
        return e != null ? e : BY_ID.get("p1_burj_sunset");
    }
    public static Map<String, Entry> all() { return BY_ID; }
}
