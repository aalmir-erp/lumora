package ae.servia.wear.watchface;

/**
 * v1.24.43 — Burj Sunset watch face (preset p1_burj_sunset).
 * Thin subclass that pins p1_burj_sunset as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace01BurjSunset extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p1_burj_sunset";
    }
}
