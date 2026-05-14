package ae.servia.wear;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * v1.24.30 — Servia Wear theme system.
 *
 * 10 curated palettes the customer can switch between from
 * ThemePickerActivity. Each theme is a (bg, surface, primary,
 * accent, text) quintuple plus an optional gradient. Tiles and
 * activities call {@link #current(Context)} to fetch the current
 * theme and apply colours.
 *
 * The customer's first saved custom-SOS button is rendered as the
 * theme's "user slot" — a round amber chip on the watch face to
 * confirm their primary SOS is one tap away regardless of which
 * theme they picked.
 */
public final class ServiaTheme {

    public static final String PREFS = "servia_theme";
    public static final String KEY_ID = "theme_id";

    public final String id;
    public final String name;
    public final String tagline;
    public final int bg;
    public final int surface;
    public final int primary;
    public final int accent;
    public final int text;
    public final int textMuted;
    public final int dividerArgb;

    private ServiaTheme(String id, String name, String tagline,
                         int bg, int surface, int primary, int accent,
                         int text, int textMuted, int dividerArgb) {
        this.id = id; this.name = name; this.tagline = tagline;
        this.bg = bg; this.surface = surface;
        this.primary = primary; this.accent = accent;
        this.text = text; this.textMuted = textMuted;
        this.dividerArgb = dividerArgb;
    }

    /** All 10 themes, listed in display order. First = default. */
    public static final ServiaTheme[] ALL = new ServiaTheme[]{
        new ServiaTheme("classic_teal", "Servia Classic",
            "Teal · amber accent · default",
            0xFF0F172A, 0xFF1E293B, 0xFF0F766E, 0xFFFCD34D,
            0xFFFFFFFF, 0xFFCBD5E1, 0x33FCD34D),
        new ServiaTheme("midnight_red", "Midnight Red",
            "SOS-first, dark slate + crimson",
            0xFF0B0F19, 0xFF1A1F2E, 0xFFDC2626, 0xFFFCA5A5,
            0xFFFFFFFF, 0xFFFCA5A5, 0x33DC2626),
        new ServiaTheme("desert_dune", "Desert Dune",
            "UAE warm sand + indigo",
            0xFF1F1B16, 0xFF2D2620, 0xFFF59E0B, 0xFF7C3AED,
            0xFFFEF3C7, 0xFFFCD34D, 0x33F59E0B),
        new ServiaTheme("ocean_glow", "Ocean Glow",
            "Deep blue + cyan glow",
            0xFF03152C, 0xFF0F2A4A, 0xFF0EA5E9, 0xFF22D3EE,
            0xFFE0F2FE, 0xFFBAE6FD, 0x3322D3EE),
        new ServiaTheme("forest_mint", "Forest Mint",
            "Green + emerald",
            0xFF052E2B, 0xFF064E3B, 0xFF10B981, 0xFFA7F3D0,
            0xFFECFDF5, 0xFFA7F3D0, 0x3310B981),
        new ServiaTheme("violet_neon", "Violet Neon",
            "Royal violet + pink neon",
            0xFF1A0B2E, 0xFF301B4F, 0xFF8B5CF6, 0xFFF472B6,
            0xFFFAE8FF, 0xFFD8B4FE, 0x33F472B6),
        new ServiaTheme("crimson_rose", "Crimson Rose",
            "Deep red + rose gold",
            0xFF1F0A0F, 0xFF2E1218, 0xFFE11D48, 0xFFFEC7B4,
            0xFFFFE4E6, 0xFFFEC7B4, 0x33E11D48),
        new ServiaTheme("carbon_silver", "Carbon Silver",
            "Pro / business · monochrome",
            0xFF111417, 0xFF1F2329, 0xFF6B7280, 0xFFE5E7EB,
            0xFFF9FAFB, 0xFFD1D5DB, 0x336B7280),
        new ServiaTheme("sunset_glow", "Sunset Glow",
            "Orange + magenta gradient",
            0xFF1F0F1A, 0xFF301727, 0xFFFB923C, 0xFFEC4899,
            0xFFFFF1E6, 0xFFFBCFE8, 0x33EC4899),
        new ServiaTheme("pearl_light", "Pearl Light",
            "Light mode · soft cream",
            0xFFF8FAFC, 0xFFFFFFFF, 0xFF0F766E, 0xFFF59E0B,
            0xFF0F172A, 0xFF475569, 0x330F766E),
    };

    /** Current theme based on SharedPreferences (defaults to classic). */
    public static ServiaTheme current(Context ctx) {
        SharedPreferences sp = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        String id = sp.getString(KEY_ID, ALL[0].id);
        for (ServiaTheme t : ALL) if (t.id.equals(id)) return t;
        return ALL[0];
    }

    public static void apply(Context ctx, String id) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
           .edit().putString(KEY_ID, id).apply();
    }
}
