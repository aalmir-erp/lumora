package ae.servia.wear.tiles;

import ae.servia.wear.ServiaTheme;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/**
 * Next-booking tile. v1: shows static placeholder. v2 (future) will fetch
 * /api/me/bookings via OkHttp and show actual ETA.
 */
public class NextBookingTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
        return wrap(theme.bg,
            col()
                .addContent(title("📋 NEXT BOOKING", theme.accent))
                .addContent(spacer(4))
                .addContent(big("—", theme.text))
                .addContent(spacer(2))
                .addContent(body("Open app to view your next booking", theme.text))
                .addContent(spacer(6))
                .addContent(body("Tap to see all", theme.accent))
                .build());
    }
}
