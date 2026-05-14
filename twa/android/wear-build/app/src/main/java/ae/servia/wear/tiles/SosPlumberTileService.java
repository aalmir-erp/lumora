package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS Plumber tile — sky blue. */
public class SosPlumberTileService extends ServiaTileBase {
    private static final int SKY = 0xFF0EA5E9;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return SosTileHelper.buildSosTile(this, SKY, WHITE, "🚿 SOS PLUMBER",
            "LEAK?", "Tap to summon nearest plumber", "plumber");
    }
}
