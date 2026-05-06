package ae.servia.wear.tiles;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/** "🎯 My Servia SOS" tile — opens the user's saved custom shortcuts. */
public class MySosTileService extends ServiaTileBase {
    private static final int INDIGO = 0xFF6366F1;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ModifiersBuilders.Clickable launch =
            new ModifiersBuilders.Clickable.Builder()
                .setId("my_sos")
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName("ae.servia.wear.MySosActivity")
                                .build())
                        .build())
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
                            .setColor(ColorBuilders.argb(INDIGO))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(20))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(12))
                            .build())
                    .setClickable(launch)
                    .build())
            .addContent(
                col()
                    .addContent(title("🎯 MY SOS", AMBER))
                    .addContent(spacer(4))
                    .addContent(big("TAP", WHITE))
                    .addContent(spacer(2))
                    .addContent(body("Your saved one-tap shortcuts", WHITE))
                    .addContent(spacer(6))
                    .addContent(body("Custom buttons created on phone", AMBER))
                    .build())
            .build();
    }
}
