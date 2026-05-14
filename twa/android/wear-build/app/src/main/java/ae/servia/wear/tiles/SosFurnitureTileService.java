package ae.servia.wear.tiles;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS Furniture Move/Fix tile — purple. */
public class SosFurnitureTileService extends ServiaTileBase {
    private static final int PURPLE = 0xFF7C3AED;
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return SosTileHelper.buildSosTile(this, PURPLE, AMBER, "📦 SOS FURNITURE",
            "MOVE / FIX", "Movers, fixers, assemblers — closest first",
            "furniture_move");
    }
}
