package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS AC tile — cyan. */
public class SosAcTileService extends ServiaTileBase {
    private static final int CYAN = 0xFF06B6D4;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return SosTileHelper.buildSosTile(this, CYAN, DARK, "❄️ SOS AC",
            "NOT COOLING?", "Servia HVAC technician on the way",
            "ac_cleaning");
    }
}
