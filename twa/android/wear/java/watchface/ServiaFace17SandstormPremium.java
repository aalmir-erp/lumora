package ae.servia.wear.watchface;

/**
 * v1.24.43 — Sandstorm Premium watch face (preset p17_sandstorm_premium).
 * Thin subclass that pins p17_sandstorm_premium as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace17SandstormPremium extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p17_sandstorm_premium";
    }
}
