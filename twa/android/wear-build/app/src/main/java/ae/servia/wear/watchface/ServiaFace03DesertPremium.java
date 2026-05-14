package ae.servia.wear.watchface;

/**
 * v1.24.43 — Desert Premium watch face (preset p3_desert_premium).
 * Thin subclass that pins p3_desert_premium as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace03DesertPremium extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p3_desert_premium";
    }
}
