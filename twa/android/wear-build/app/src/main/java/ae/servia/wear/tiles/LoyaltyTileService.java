package ae.servia.wear.tiles;

import ae.servia.wear.ServiaTheme;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** Loyalty tier tile — current Ambassador status. */
public class LoyaltyTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
        return wrap(theme.primary,
            col()
                .addContent(title("🏆 AMBASSADOR", DARK))
                .addContent(spacer(4))
                .addContent(big("BRONZE", theme.text))
                .addContent(spacer(2))
                .addContent(body("5% off every booking", theme.text))
                .addContent(spacer(6))
                .addContent(body("Refer 5 → Silver · 12% off", DARK))
                .build());
    }
}
