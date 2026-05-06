package ae.servia.wear.tiles;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/**
 * v1.24.15 — Servia HUB tile.
 *
 * Single tile, FOUR tappable buttons in a 2×2 grid — fits the entire
 * watch face round screen. Each quadrant launches a different Servia
 * activity. Replaces the previous "one full-screen tile per action"
 * pattern that wasted screen space (user complaint: "instead of having
 * full screen big tile why dont we make multiple tiles also in one view
 * user can add buttons of his choice in one tile like many other apps").
 *
 * Quadrants (current static set):
 *   ┌──────────┬──────────┐
 *   │ 🎙 TALK  │ 🆘 SOS   │
 *   │  yellow  │   red    │
 *   ├──────────┼──────────┤
 *   │ 🎯 MY    │ 🛠 ALL   │
 *   │  indigo  │  slate   │
 *   └──────────┴──────────┘
 *
 * Future: read user preferences from /api/sos/custom/me and let them
 * pick which 4 buttons fill the hub (incl. their custom shortcuts).
 */
public class HubTileService extends ServiaTileBase {

    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        // Two rows, two quadrants each
        return new LayoutElementBuilders.Column.Builder()
            .setWidth(DimensionBuilders.expand())
            .setHeight(DimensionBuilders.expand())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .addContent(
                new LayoutElementBuilders.Row.Builder()
                    .setWidth(DimensionBuilders.expand())
                    .setHeight(DimensionBuilders.weight(1))
                    .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
                    .addContent(quadrant(0xFFF59E0B, DARK,  "🎙",  "Talk",  "VoiceAssistantActivity", "talk"))
                    .addContent(spacer(2))
                    .addContent(quadrant(0xFFDC2626, AMBER, "🆘",  "SOS",   "SosCategoryGridActivity", "sos"))
                    .build())
            .addContent(spacer(2))
            .addContent(
                new LayoutElementBuilders.Row.Builder()
                    .setWidth(DimensionBuilders.expand())
                    .setHeight(DimensionBuilders.weight(1))
                    .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
                    .addContent(quadrant(0xFF6366F1, AMBER, "🎯", "My SOS", "MySosActivity",      "mysos"))
                    .addContent(spacer(2))
                    .addContent(quadrant(0xFF334155, AMBER, "🛠",  "All",    "AllServicesActivity", "all"))
                    .build())
            .build();
    }

    /** A single tappable quadrant — 50% width, full available height. */
    private LayoutElementBuilders.LayoutElement quadrant(
            int bg, int fg, String emoji, String label, String activity, String tag) {
        ModifiersBuilders.Clickable click =
            new ModifiersBuilders.Clickable.Builder()
                .setId("hub_" + tag)
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName("ae.servia.wear." + activity)
                                .build())
                        .build())
                .build();

        return new LayoutElementBuilders.Box.Builder()
            .setWidth(DimensionBuilders.weight(1))
            .setHeight(DimensionBuilders.expand())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
            .setModifiers(
                new ModifiersBuilders.Modifiers.Builder()
                    .setBackground(
                        new ModifiersBuilders.Background.Builder()
                            .setColor(ColorBuilders.argb(bg))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(14))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(4))
                            .build())
                    .setClickable(click)
                    .build())
            .addContent(
                new LayoutElementBuilders.Column.Builder()
                    .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
                    .addContent(
                        new LayoutElementBuilders.Text.Builder()
                            .setText(emoji)
                            .setFontStyle(
                                new LayoutElementBuilders.FontStyle.Builder()
                                    .setSize(DimensionBuilders.sp(24))
                                    .build())
                            .build())
                    .addContent(spacer(2))
                    .addContent(
                        new LayoutElementBuilders.Text.Builder()
                            .setText(label)
                            .setFontStyle(
                                new LayoutElementBuilders.FontStyle.Builder()
                                    .setSize(DimensionBuilders.sp(11))
                                    .setWeight(LayoutElementBuilders.FONT_WEIGHT_BOLD)
                                    .setColor(ColorBuilders.argb(fg))
                                    .build())
                            .setMaxLines(1)
                            .build())
                    .build())
            .build();
    }
}
