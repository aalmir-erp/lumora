package ae.servia.wear.watchface;

/**
 * v1.24.43 — Violet Chronograph watch face (preset p18_violet_chrono).
 * Thin subclass that pins p18_violet_chrono as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace18VioletChrono extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p18_violet_chrono";
    }
}
