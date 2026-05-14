package ae.servia.wear.watchface;

/**
 * v1.24.43 — Servia Hours watch face (preset p21_servia_hours).
 * Thin subclass that pins p21_servia_hours as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace21ServiaHours extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p21_servia_hours";
    }
}
