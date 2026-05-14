package ae.servia.wear.watchface;

/**
 * v1.24.43 — registers all 22 watch face presets with their metadata.
 *
 * NOTE: resource references are STRINGS (e.g. "wf_frame_p01") not
 * R.drawable.* int constants, so this class compiles in BOTH packages —
 * the main Servia Wear (ae.servia.wear) AND the standalone Servia
 * Faces (ae.servia.wear.faces). Renderer resolves to int via
 * Resources.getIdentifier() at runtime.
 */
public final class WatchFaceRegistry {
    private WatchFaceRegistry() {}

    public static final String[] ALL_IDS = {
        "p1_burj_sunset",
        "p2_marina_neon",
        "p3_desert_premium",
        "p4_sport_pulse",
        "p5_emergency_red",
        "p6_modular_dark",
        "p7_neon_grid",
        "p8_calligraphy_gold",
        "p9_pearl_ladies",
        "p10_eco_botanical",
        "p11_minimal_white",
        "p12_falcon_premium",
        "p13_pixel_retro",
        "p14_carbon_fiber",
        "p15_kids_fun",
        "p16_business_exec",
        "p17_sandstorm_premium",
        "p18_violet_chrono",
        "p19_ocean_animated",
        "p20_aviation",
        "p21_servia_hours",
        "p22_servia_dial",
    };

    public static void init() {
        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p1_burj_sunset", "Burj Sunset",
            "wf_frame_p01", "wf_preview_p01",
            240.0f, 190.0f, 92, 0xFFFFFFFF,
            900, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p2_marina_neon", "Marina Neon",
            "wf_frame_p02", "wf_preview_p02",
            240.0f, 245.0f, 86, 0xFFFFFFFF,
            200, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p3_desert_premium", "Desert Premium",
            "wf_frame_p03", "wf_preview_p03",
            240.0f, 225.0f, 88, 0xFFFEF3C7,
            800, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p4_sport_pulse", "Sport Pulse",
            "wf_frame_p04", "wf_preview_p04",
            240.0f, 220.0f, 58, 0xFFFFFFFF,
            900, -2.00f,
            true, false, true));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p5_emergency_red", "Emergency Red",
            "wf_frame_p05", "wf_preview_p05",
            240.0f, 230.0f, 74, 0xFFFFFFFF,
            900, -2.00f,
            false, true, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p6_modular_dark", "Modular Pro",
            "wf_frame_p06", "wf_preview_p06",
            40.0f, 120.0f, 84, 0xFFFFFFFF,
            800, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p7_neon_grid", "Neon Grid",
            "wf_frame_p07", "wf_preview_p07",
            240.0f, 230.0f, 88, 0xFFFFFFFF,
            900, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p8_calligraphy_gold", "Calligraphy Gold",
            "wf_frame_p08", "wf_preview_p08",
            240.0f, 250.0f, 100, 0xFFFCD34D,
            900, -2.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p9_pearl_ladies", "Pearl Ladies",
            "wf_frame_p09", "wf_preview_p09",
            370.0f, 370.0f, 18, 0xFFFFFFFF,
            700, 0.00f,
            true, false, true));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p10_eco_botanical", "Eco Botanical",
            "wf_frame_p10", "wf_preview_p10",
            370.0f, 370.0f, 18, 0xFF022C22,
            700, 0.00f,
            true, false, true));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p11_minimal_white", "Minimal White",
            "wf_frame_p11", "wf_preview_p11",
            240.0f, 230.0f, 120, 0xFF0F172A,
            100, -6.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p12_falcon_premium", "Falcon Premium",
            "wf_frame_p12", "wf_preview_p12",
            240.0f, 240.0f, 80, 0xFFFFFFFF,
            700, 0.00f,
            false, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p13_pixel_retro", "Pixel Retro",
            "wf_frame_p13", "wf_preview_p13",
            360.0f, 345.0f, 20, 0xFF0F172A,
            700, 0.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p14_carbon_fiber", "Carbon Fiber",
            "wf_frame_p14", "wf_preview_p14",
            240.0f, 230.0f, 86, 0xFFFFFFFF,
            500, -2.00f,
            false, true, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p15_kids_fun", "Kids Fun",
            "wf_frame_p15", "wf_preview_p15",
            240.0f, 230.0f, 100, 0xFFFFFFFF,
            900, -2.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p16_business_exec", "Business Exec",
            "wf_frame_p16", "wf_preview_p16",
            40.0f, 120.0f, 80, 0xFFFFFFFF,
            800, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p17_sandstorm_premium", "Sandstorm Premium",
            "wf_frame_p17", "wf_preview_p17",
            240.0f, 210.0f, 92, 0xFFFFFFFF,
            800, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p18_violet_chrono", "Violet Chronograph",
            "wf_frame_p18", "wf_preview_p18",
            240.0f, 190.0f, 74, 0xFFFFFFFF,
            900, -2.00f,
            true, false, true));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p19_ocean_animated", "Ocean Live",
            "wf_frame_p19", "wf_preview_p19",
            240.0f, 255.0f, 86, 0xFFFFFFFF,
            100, -3.00f,
            true, false, false));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p20_aviation", "Aviation",
            "wf_frame_p20", "wf_preview_p20",
            240.0f, 230.0f, 56, 0xFFFFFFFF,
            900, -1.00f,
            false, true, true));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p21_servia_hours", "Servia Hours",
            "wf_frame_p21", "wf_preview_p21",
            150.0f, 91.1f, 22, 0xFFFFFFFF,
            700, 0.00f,
            false, false, true));

        WatchFaceMeta.put(new WatchFaceMeta.Entry(
            "p22_servia_dial", "Servia Dial",
            "wf_frame_p22", "wf_preview_p22",
            240.0f, 180.0f, 106, 0xFFFFFFFF,
            900, -4.00f,
            true, false, false));

    }
}
