package ae.servia.wear.tiles;

import ae.servia.wear.ServiaTheme;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/** "🛠 All Services" tile — opens 4-icon-per-screen scrollable grid. */
public class AllServicesTileService extends ServiaTileBase {
    private static final int SLATE = 0xFF334155;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
        ModifiersBuilders.Clickable launch =
            new ModifiersBuilders.Clickable.Builder()
                .setId("all_services")
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName("ae.servia.wear.AllServicesActivity")
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
                            .setColor(ColorBuilders.argb(SLATE))
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
                    .addContent(title("🛠 SERVICES", theme.accent))
                    .addContent(spacer(4))
                    .addContent(big("ALL 8", theme.text))
                    .addContent(spacer(2))
                    .addContent(body("Tow · plumber · electric · AC · clean", theme.text))
                    .addContent(spacer(6))
                    .addContent(body("4 per screen · scroll · tap to order", theme.accent))
                    .build())
            .build();
    }
}
