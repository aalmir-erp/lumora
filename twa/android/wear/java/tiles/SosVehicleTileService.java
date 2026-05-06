package ae.servia.wear.tiles;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/** SOS Vehicle Recovery tile — red, big TAP target, fires RecoveryActivity. */
public class SosVehicleTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        return SosTileHelper.buildSosTile(this, RED, AMBER, "🚗 SOS VEHICLE",
            "BREAKDOWN?", "GPS sent · closest tow truck dispatched",
            "vehicle_recovery");
    }
}
