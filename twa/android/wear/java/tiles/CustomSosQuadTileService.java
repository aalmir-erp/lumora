package ae.servia.wear.tiles;

import android.content.SharedPreferences;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

import ae.servia.wear.ServiaTheme;

/**
 * v1.24.30 — QuadTile: 4 small circular clickable buttons in ONE tile.
 *
 * Samsung Health "Together" / "Exercise" pattern (per user spec). Each
 * mini-button binds to one of the customer's first 4 saved custom SOS
 * shortcuts (slots 1..4 in SharedPreferences "servia_csos_slots").
 *
 * Why one tile instead of five separate ones?
 *   - Tile picker fatigue: 5 separate Slot tiles plus the existing 14
 *     was overwhelming. A single QuadTile is one entry that delivers
 *     4 one-tap actions.
 *   - Glanceable: 2×2 grid means you see all your shortcuts at once.
 *
 * Slot 5 still exists as its own tile for power users; this one
 * collapses 1-4 into a single screen for everyone else.
 *
 * Empty slots show "+" and open CustomSosCreateActivity.
 * Bound slots dispatch directly via CustomSosSlotDispatchActivity.
 */
public class CustomSosQuadTileService extends ServiaTileBase {

    private static final int[] BG = {
        0xFFDC2626,  // red - slot 1
        0xFFF59E0B,  // amber - slot 2
        0xFF0EA5E9,  // sky - slot 3
        0xFF8B5CF6,  // violet - slot 4
    };
    private static final int EMPTY_BG = 0xFF334155;

    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(
            RequestBuilders.TileRequest req) {

        ServiaTheme theme = ServiaTheme.current(this);
        SharedPreferences sp = getSharedPreferences(
            "servia_csos_slots", MODE_PRIVATE);

        LayoutElementBuilders.Row.Builder row1 = newRow();
        row1.addContent(miniButton(sp, 1, BG[0]))
            .addContent(spacerW(6))
            .addContent(miniButton(sp, 2, BG[1]));

        LayoutElementBuilders.Row.Builder row2 = newRow();
        row2.addContent(miniButton(sp, 3, BG[2]))
            .addContent(spacerW(6))
            .addContent(miniButton(sp, 4, BG[3]));

        LayoutElementBuilders.Column col = col()
            .addContent(title("⚡ MY 4 SHORTCUTS", theme.accent))
            .addContent(spacer(6))
            .addContent(row1.build())
            .addContent(spacer(6))
            .addContent(row2.build())
            .build();

        return new LayoutElementBuilders.Box.Builder()
            .setWidth(DimensionBuilders.expand())
            .setHeight(DimensionBuilders.expand())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
            .setModifiers(
                new ModifiersBuilders.Modifiers.Builder()
                    .setBackground(
                        new ModifiersBuilders.Background.Builder()
                            .setColor(ColorBuilders.argb(theme.bg))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(20))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(10))
                            .build())
                    .build())
            .addContent(col)
            .build();
    }

    private LayoutElementBuilders.Box miniButton(
            SharedPreferences sp, int slot, int defaultBg) {

        int btnId = sp.getInt("csos_slot_" + slot + "_id", 0);
        String label = sp.getString("csos_slot_" + slot + "_label", null);
        String emoji = sp.getString("csos_slot_" + slot + "_emoji", null);
        boolean bound = btnId > 0 && label != null;

        ModifiersBuilders.Clickable click;
        if (bound) {
            click = new ModifiersBuilders.Clickable.Builder()
                .setId("quad_slot_" + slot)
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName(
                                    "ae.servia.wear.CustomSosSlotDispatchActivity")
                                .addKeyToExtraMapping(
                                    "slot",
                                    new ActionBuilders.AndroidIntExtra.Builder()
                                        .setValue(slot)
                                        .build())
                                .build())
                        .build())
                .build();
        } else {
            click = new ModifiersBuilders.Clickable.Builder()
                .setId("quad_create_" + slot)
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName(
                                    "ae.servia.wear.CustomSosCreateActivity")
                                .build())
                        .build())
                .build();
        }

        // Inner column: emoji on top, short label below
        LayoutElementBuilders.Column inner = col()
            .addContent(new LayoutElementBuilders.Text.Builder()
                .setText(bound ? (emoji == null ? "🆘" : emoji) : "+")
                .setFontStyle(new LayoutElementBuilders.FontStyle.Builder()
                    .setSize(DimensionBuilders.sp(20))
                    .setColor(ColorBuilders.argb(WHITE))
                    .build())
                .setMaxLines(1)
                .build())
            .addContent(spacer(2))
            .addContent(new LayoutElementBuilders.Text.Builder()
                .setText(bound ? trim(label, 7) : "Add")
                .setFontStyle(new LayoutElementBuilders.FontStyle.Builder()
                    .setSize(DimensionBuilders.sp(9))
                    .setWeight(LayoutElementBuilders.FONT_WEIGHT_BOLD)
                    .setColor(ColorBuilders.argb(WHITE))
                    .build())
                .setMaxLines(1)
                .build())
            .build();

        return new LayoutElementBuilders.Box.Builder()
            .setWidth(DimensionBuilders.dp(64))
            .setHeight(DimensionBuilders.dp(64))
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
            .setModifiers(
                new ModifiersBuilders.Modifiers.Builder()
                    .setBackground(
                        new ModifiersBuilders.Background.Builder()
                            .setColor(ColorBuilders.argb(
                                bound ? defaultBg : EMPTY_BG))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(32))
                                    .build())
                            .build())
                    .setClickable(click)
                    .build())
            .addContent(inner)
            .build();
    }

    private LayoutElementBuilders.Row.Builder newRow() {
        return new LayoutElementBuilders.Row.Builder()
            .setWidth(DimensionBuilders.wrap())
            .setHeight(DimensionBuilders.wrap())
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER);
    }

    private LayoutElementBuilders.Spacer spacerW(int dp) {
        return new LayoutElementBuilders.Spacer.Builder()
            .setWidth(DimensionBuilders.dp(dp))
            .build();
    }

    private String trim(String s, int max) {
        if (s == null) return "";
        return s.length() <= max ? s : s.substring(0, max - 1) + "…";
    }
}
