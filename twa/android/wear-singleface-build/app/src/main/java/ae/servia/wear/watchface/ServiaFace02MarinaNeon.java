package ae.servia.wear.watchface;

/**
 * v1.24.43 — Marina Neon watch face (preset p2_marina_neon).
 * Thin subclass that pins p2_marina_neon as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace02MarinaNeon extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p2_marina_neon";
    }
}
