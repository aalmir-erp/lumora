package ae.servia.wear.watchface;

/**
 * v1.24.43 — Minimal White watch face (preset p11_minimal_white).
 * Thin subclass that pins p11_minimal_white as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace11MinimalWhite extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p11_minimal_white";
    }
}
