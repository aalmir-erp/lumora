package ae.servia.wear.tiles;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

import ae.servia.wear.ServiaTheme;

/** "🎯 My Servia SOS" tile — opens the user's saved custom shortcuts. */
public class MySosTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
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
                            .setColor(ColorBuilders.argb(theme.primary))
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
                    .addContent(title("🎯 MY SOS", theme.accent))
                    .addContent(spacer(4))
                    .addContent(big("TAP", theme.text))
                    .addContent(spacer(2))
                    .addContent(body("Your saved shortcuts", theme.text))
                    .addContent(spacer(6))
                    .addContent(body("Auto-syncs from phone", theme.accent))
                    .build())
            .build();
    }
}
