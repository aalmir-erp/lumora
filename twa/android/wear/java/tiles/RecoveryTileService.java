package ae.servia.wear.tiles;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/**
 * SOS recovery tile — large red panic button.
 *
 * v1.24.1: tapping the tile now launches RecoveryActivity directly
 * (instead of bouncing through the launcher), which captures real GPS
 * and dispatches the closest recovery vendor in one round-trip.
 */
public class RecoveryTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        // Build a clickable wrapper so the entire tile is one giant SOS button.
        ModifiersBuilders.Clickable launchRecovery =
            new ModifiersBuilders.Clickable.Builder()
                .setId("sos_recovery")
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                // v1.24.7 — go to the 8-tile category grid
                                // (matches /sos.html on the website) instead
                                // of dispatching vehicle recovery blindly.
                                .setClassName("ae.servia.wear.SosCategoryGridActivity")
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
                            .setColor(androidx.wear.protolayout.ColorBuilders.argb(RED))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(20))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(12))
                            .build())
                    .setClickable(launchRecovery)
                    .build())
            .addContent(
                col()
                    .addContent(title("🆘 SERVIA SOS", AMBER))
                    .addContent(spacer(4))
                    .addContent(big("TAP", WHITE))
                    .addContent(spacer(2))
                    .addContent(body("8 services · pick what you need", WHITE))
                    .addContent(spacer(6))
                    .addContent(body("Vehicle · plumber · electrician · AC · more", AMBER))
                    .build())
            .build();
    }
}
