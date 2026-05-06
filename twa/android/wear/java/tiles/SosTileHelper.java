package ae.servia.wear.tiles;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;

/**
 * Shared builder for every SOS-style tile. All SOS category tiles
 * (vehicle / furniture / electrician / plumber / AC / handyman) get
 * the SAME big-red-button look + same clickable-Box launch into
 * SosLauncherActivity, just with different colour, label, and the
 * service_id passed via Intent extra.
 *
 * Keeps each tile-service class to ~5 lines so adding a new SOS
 * category is trivial (copy a class, change 3 strings).
 */
public final class SosTileHelper {
    private SosTileHelper() {}

    public static LayoutElementBuilders.LayoutElement buildSosTile(
            ServiaTileBase host,
            int bgColor, int accentColor,
            String headline, String big, String sub,
            String serviceId) {

        ModifiersBuilders.Clickable launch =
            new ModifiersBuilders.Clickable.Builder()
                .setId("sos_" + serviceId)
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName("ae.servia.wear.SosLauncherActivity")
                                .addKeyToExtraMapping("service_id",
                                    new ActionBuilders.AndroidStringExtra.Builder()
                                        .setValue(serviceId).build())
                                .addKeyToExtraMapping("category_label",
                                    new ActionBuilders.AndroidStringExtra.Builder()
                                        .setValue(headline).build())
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
                            .setColor(ColorBuilders.argb(bgColor))
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
                host.col()
                    .addContent(host.title(headline, accentColor))
                    .addContent(host.spacer(4))
                    .addContent(host.big(big, accentColor))
                    .addContent(host.spacer(2))
                    .addContent(host.body(sub, accentColor))
                    .addContent(host.spacer(6))
                    .addContent(host.body("Tap to dispatch · GPS · vendor in seconds", accentColor))
                    .build())
            .build();
    }
}
