package ae.servia.wear.watchface;

/**
 * v1.24.43 — Calligraphy Gold watch face (preset p8_calligraphy_gold).
 * Thin subclass that pins p8_calligraphy_gold as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace08CalligraphyGold extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p8_calligraphy_gold";
    }
}
