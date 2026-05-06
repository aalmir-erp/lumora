package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/**
 * Next-booking tile. v1: shows static placeholder. v2 (future) will fetch
 * /api/me/bookings via OkHttp and show actual ETA.
 */
public class NextBookingTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return wrap(DARK,
            col()
                .addContent(title("📋 NEXT BOOKING", AMBER))
                .addContent(spacer(4))
                .addContent(big("—", WHITE))
                .addContent(spacer(2))
                .addContent(body("Open app to view your next booking", WHITE))
                .addContent(spacer(6))
                .addContent(body("Tap to see all", AMBER))
                .build());
    }
}
