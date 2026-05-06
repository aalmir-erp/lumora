package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** Quick-book tile: one-tap to start booking your most-used service. */
public class QuickBookTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return wrap(TEAL,
            col()
                .addContent(title("⚡ QUICK BOOK", AMBER))
                .addContent(spacer(4))
                .addContent(big("Tap", WHITE))
                .addContent(spacer(2))
                .addContent(body("Most-used: Deep Clean · AED 350+", WHITE))
                .addContent(spacer(6))
                .addContent(body("Tap to book on phone", AMBER))
                .build());
    }
}
