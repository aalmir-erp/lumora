package ae.servia.wear.tiles;

import ae.servia.wear.ServiaTheme;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** Wallet balance tile — current AED balance. */
public class WalletTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
        return wrap(theme.primary,
            col()
                .addContent(title("💰 WALLET", DARK))
                .addContent(spacer(4))
                .addContent(big("AED —", theme.text))
                .addContent(spacer(2))
                .addContent(body("Tap to top up via NFC pay", theme.text))
                .addContent(spacer(6))
                .addContent(body("Sync from phone app", DARK))
                .build());
    }
}
