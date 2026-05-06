package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS Electrician tile — yellow. */
public class SosElectricianTileService extends ServiaTileBase {
    private static final int YELLOW = 0xFFFBBF24;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return SosTileHelper.buildSosTile(this, YELLOW, DARK, "🔌 SOS ELECTRIC",
            "NO POWER?", "Servia electrician dispatched in minutes",
            "electrician");
    }
}
