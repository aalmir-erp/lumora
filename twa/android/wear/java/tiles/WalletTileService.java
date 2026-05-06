package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** Wallet balance tile — current AED balance. */
public class WalletTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return wrap(TEAL_LIGHT,
            col()
                .addContent(title("💰 WALLET", DARK))
                .addContent(spacer(4))
                .addContent(big("AED —", WHITE))
                .addContent(spacer(2))
                .addContent(body("Tap to top up via NFC pay", WHITE))
                .addContent(spacer(6))
                .addContent(body("Sync from phone app", DARK))
                .build());
    }
}
