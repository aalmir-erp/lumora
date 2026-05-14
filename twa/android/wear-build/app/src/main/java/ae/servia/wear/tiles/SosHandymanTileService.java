package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS Handyman tile — green. */
public class SosHandymanTileService extends ServiaTileBase {
    private static final int GREEN = 0xFF16A34A;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return SosTileHelper.buildSosTile(this, GREEN, WHITE, "🔧 SOS HANDYMAN",
            "FIX IT NOW", "Wall paint · door · curtain rod · TV mount",
            "handyman");
    }
}
