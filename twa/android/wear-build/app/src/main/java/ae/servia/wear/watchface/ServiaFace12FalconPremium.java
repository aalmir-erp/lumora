package ae.servia.wear.watchface;

/**
 * v1.24.43 — Falcon Premium watch face (preset p12_falcon_premium).
 * Thin subclass that pins p12_falcon_premium as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace12FalconPremium extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p12_falcon_premium";
    }
}
