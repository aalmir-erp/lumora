package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS recovery tile — large red panic button. */
public class RecoveryTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return wrap(RED,
            col()
                .addContent(title("🆘 SOS RECOVERY", AMBER))
                .addContent(spacer(4))
                .addContent(big("TAP", WHITE))
                .addContent(spacer(2))
                .addContent(body("Breakdown? GPS captured + truck dispatched.", WHITE))
                .addContent(spacer(6))
                .addContent(body("AED 250 · 24/7 · 18-min ETA", AMBER))
                .build());
    }
}
