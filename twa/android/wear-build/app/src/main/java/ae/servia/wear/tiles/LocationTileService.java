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
 * v1.24.29 — "📍 Address" tile. Shows the customer's current saved area
 * + emirate. Tap → LocationActivity (refresh GPS / edit on phone).
 *
 * Reads SharedPreferences "servia_address" populated by
 * {@link ae.servia.wear.LocationActivity#pushLocation}.
 */
public class LocationTileService extends ServiaTileBase {

    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(
            RequestBuilders.TileRequest req) {

        ServiaTheme theme = ServiaTheme.current(this);
        SharedPreferences sp = getSharedPreferences(
            "servia_address", MODE_PRIVATE);
        String area = sp.getString("area", null);
        String emirate = sp.getString("emirate", null);

        ModifiersBuilders.Clickable click =
            new ModifiersBuilders.Clickable.Builder()
                .setId("address")
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName("ae.servia.wear.LocationActivity")
                                .build())
                        .build())
                .build();

        LayoutElementBuilders.Column.Builder content = col()
            .addContent(title("📍 ADDRESS", theme.accent))
            .addContent(spacer(6));

        if (area != null && !area.isEmpty()) {
            content.addContent(big(area, theme.text))
                   .addContent(spacer(2));
            if (emirate != null && !emirate.isEmpty()) {
                content.addContent(body(emirate, theme.accent));
            }
            content.addContent(spacer(6))
                   .addContent(body("Tap to refresh GPS", theme.text));
        } else {
            content.addContent(big("(set)", theme.text))
                   .addContent(spacer(4))
                   .addContent(body("Tap to capture\nyour location", theme.text));
        }

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
                    .setClickable(click)
                    .build())
            .addContent(content.build())
            .build();
    }
}
