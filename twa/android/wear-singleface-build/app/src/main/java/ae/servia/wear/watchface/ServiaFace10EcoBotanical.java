package ae.servia.wear.watchface;

/**
 * v1.24.43 — Eco Botanical watch face (preset p10_eco_botanical).
 * Thin subclass that pins p10_eco_botanical as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace10EcoBotanical extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p10_eco_botanical";
    }
}
