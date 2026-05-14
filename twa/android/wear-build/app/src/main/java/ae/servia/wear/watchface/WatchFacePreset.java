package ae.servia.wear.watchface;

import ae.servia.wear.ServiaTheme;

/**
 * v1.24.33 — Servia watch-face preset.
 *
 * A preset is the combination of a colour theme + a face layout +
 * default slot assignments. The user picks one preset from the 10
 * curated options in {@link #ALL}, then can edit individual slots
 * to override the defaults.
 *
 * Layouts:
 *   DIGITAL_LARGE  — big 64sp time, vertical date, 4-slot bottom row
 *   DIGITAL_SMALL  — compact 36sp time top, 6 slots arranged below
 *   ANALOG         — classic dial with hour/minute/second hands +
 *                    4 slots (top-left, top-right, bottom-left, bottom-right)
 *   HYBRID         — analog dial with 1 small digital readout + 4 slots
 *   MINIMAL        — single line "HH:MM" centred, 2 slots only
 *
 * Slot positions are normalised (0..1) so layouts scale across
 * 360 / 384 / 454 px Wear screens.
 */
public final class WatchFacePreset {

    public enum Layout {
        DIGITAL_LARGE, DIGITAL_SMALL, ANALOG, HYBRID, MINIMAL,
        // v1.24.35 — animated, brand-themed layouts. Each runs at ~30 fps in
        // active/interactive mode. Falls back to a static frame in ambient.
        SANDSTORM,         // drifting sand particles, AC-service warm gold
        BURJ_SKYLINE,      // animated city silhouette + twinkling lights
        MARINA_PULSE,      // expanding ripple per second tick, water blue
        FALCON_TRAIL,      // UAE falcon icon orbits the time
        SERVICE_SPOTLIGHT  // rotating beam highlights one slot at a time
    }

    public final String id;
    public final String name;
    public final ServiaTheme theme;
    public final Layout layout;
    /** Default slot assignments (0..N-1 entries). Each entry is a SlotKind id. */
    public final String[] defaultSlots;

    private WatchFacePreset(String id, String name, ServiaTheme theme,
                             Layout layout, String[] defaultSlots) {
        this.id = id; this.name = name; this.theme = theme;
        this.layout = layout; this.defaultSlots = defaultSlots;
    }

    /**
     * 10 curated presets. Mix of layouts × themes so the user gets
     * meaningful variety in the picker, not 10 lookalikes.
     */
    public static final WatchFacePreset[] ALL = new WatchFacePreset[]{
        new WatchFacePreset("p1_classic_lg",   "Classic Bold",
            ServiaTheme.ALL[0], Layout.DIGITAL_LARGE,
            new String[]{"sos_1", "talk",   "book",   "address"}),
        new WatchFacePreset("p2_red_minimal",  "SOS Minimal",
            ServiaTheme.ALL[1], Layout.MINIMAL,
            new String[]{"sos_1", "sos_2"}),
        new WatchFacePreset("p3_desert_sm",    "Desert Compact",
            ServiaTheme.ALL[2], Layout.DIGITAL_SMALL,
            new String[]{"sos_1", "sos_2", "talk", "weather", "steps", "wallet"}),
        new WatchFacePreset("p4_ocean_hybrid", "Ocean Hybrid",
            ServiaTheme.ALL[3], Layout.HYBRID,
            new String[]{"weather", "next_booking", "talk", "sos_1"}),
        new WatchFacePreset("p5_forest_analog","Forest Analog",
            ServiaTheme.ALL[4], Layout.ANALOG,
            new String[]{"sos_1", "talk", "address", "wallet"}),
        new WatchFacePreset("p6_violet_lg",    "Violet Bold",
            ServiaTheme.ALL[5], Layout.DIGITAL_LARGE,
            new String[]{"sos_1", "sos_2", "sos_3", "sos_4"}),
        new WatchFacePreset("p7_crimson_sm",   "Crimson Compact",
            ServiaTheme.ALL[6], Layout.DIGITAL_SMALL,
            new String[]{"sos_1", "sos_2", "sos_3", "sos_4", "talk", "track"}),
        new WatchFacePreset("p8_carbon_min",   "Carbon Minimal",
            ServiaTheme.ALL[7], Layout.MINIMAL,
            new String[]{"talk", "sos_1"}),
        new WatchFacePreset("p9_sunset_hybrid","Sunset Hybrid",
            ServiaTheme.ALL[8], Layout.HYBRID,
            new String[]{"weather", "battery", "sos_1", "talk"}),
        new WatchFacePreset("p10_pearl_analog","Pearl Analog",
            ServiaTheme.ALL[9], Layout.ANALOG,
            new String[]{"sos_1", "address", "wallet", "talk"}),
        // v1.24.35 — 5 animated, brand-themed variants
        new WatchFacePreset("p11_sandstorm",   "Sandstorm Live",
            ServiaTheme.ALL[2], Layout.SANDSTORM,
            new String[]{"sos_1", "talk", "weather", "battery"}),
        new WatchFacePreset("p12_burj",        "Burj Skyline",
            ServiaTheme.ALL[3], Layout.BURJ_SKYLINE,
            new String[]{"sos_1", "next_booking", "talk", "track"}),
        new WatchFacePreset("p13_marina",      "Marina Pulse",
            ServiaTheme.ALL[3], Layout.MARINA_PULSE,
            new String[]{"sos_1", "address", "talk", "weather"}),
        new WatchFacePreset("p14_falcon",      "Falcon Trail",
            ServiaTheme.ALL[1], Layout.FALCON_TRAIL,
            new String[]{"sos_1", "talk", "track", "wallet"}),
        new WatchFacePreset("p15_spotlight",   "Service Spotlight",
            ServiaTheme.ALL[8], Layout.SERVICE_SPOTLIGHT,
            new String[]{"sos_1", "sos_2", "sos_3", "sos_4"}),
    };

    public static WatchFacePreset byId(String id) {
        if (id == null) return ALL[0];
        for (WatchFacePreset p : ALL) if (p.id.equals(id)) return p;
        return ALL[0];
    }

    /** Slot count for each layout. */
    public int slotCount() {
        switch (layout) {
            case DIGITAL_LARGE:      return 4;
            case DIGITAL_SMALL:      return 6;
            case ANALOG:             return 4;
            case HYBRID:             return 4;
            case MINIMAL:            return 2;
            case SANDSTORM:          return 4;  // bottom row
            case BURJ_SKYLINE:       return 4;  // base of skyline
            case MARINA_PULSE:       return 4;  // 4 corners
            case FALCON_TRAIL:       return 4;  // 4 corners
            case SERVICE_SPOTLIGHT:  return 4;  // 4 corners (highlighted in turn)
        }
        return 0;
    }

    /**
     * Normalised (x, y) slot centre on a 1.0 × 1.0 face. Caller
     * multiplies by canvas width / height. Returned in 0.0..1.0.
     */
    public float[] slotPosition(int slotIndex) {
        switch (layout) {
            case DIGITAL_LARGE:
                return new float[]{0.20f + slotIndex * 0.20f, 0.78f};
            case DIGITAL_SMALL:
                if (slotIndex < 3) return new float[]{0.20f + slotIndex * 0.30f, 0.62f};
                return new float[]{0.20f + (slotIndex - 3) * 0.30f, 0.82f};
            case ANALOG:
            case HYBRID:
            case MARINA_PULSE:
            case FALCON_TRAIL:
            case SERVICE_SPOTLIGHT: {
                float[][] corners = {{0.20f, 0.20f}, {0.80f, 0.20f},
                                     {0.20f, 0.80f}, {0.80f, 0.80f}};
                return corners[slotIndex % 4];
            }
            case MINIMAL:
                return slotIndex == 0 ? new float[]{0.30f, 0.85f}
                                       : new float[]{0.70f, 0.85f};
            case SANDSTORM:
                return new float[]{0.20f + slotIndex * 0.20f, 0.84f};
            case BURJ_SKYLINE:
                return new float[]{0.18f + slotIndex * 0.21f, 0.86f};
        }
        return new float[]{0.5f, 0.5f};
    }

    /** Slot pixel radius (relative to face size). */
    public float slotRadiusFraction() {
        switch (layout) {
            case DIGITAL_LARGE:      return 0.085f;
            case DIGITAL_SMALL:      return 0.075f;
            case ANALOG:             return 0.090f;
            case HYBRID:             return 0.090f;
            case MINIMAL:            return 0.110f;
            case SANDSTORM:          return 0.080f;
            case BURJ_SKYLINE:       return 0.080f;
            case MARINA_PULSE:       return 0.085f;
            case FALCON_TRAIL:       return 0.085f;
            case SERVICE_SPOTLIGHT:  return 0.085f;
        }
        return 0.080f;
    }

    /** Whether the layout has animated drawing (30fps in active mode). */
    public boolean isAnimated() {
        switch (layout) {
            case SANDSTORM: case BURJ_SKYLINE: case MARINA_PULSE:
            case FALCON_TRAIL: case SERVICE_SPOTLIGHT:
                return true;
            default:
                return false;
        }
    }
}
