package ae.servia.wear.watchface;

/**
 * v1.24.43 — Modular Pro watch face (preset p6_modular_dark).
 * Thin subclass that pins p6_modular_dark as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace06ModularDark extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p6_modular_dark";
    }
}
