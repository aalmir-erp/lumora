package ae.servia.wear.watchface;

/**
 * v1.24.43 — Neon Grid watch face (preset p7_neon_grid).
 * Thin subclass that pins p7_neon_grid as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace07NeonGrid extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p7_neon_grid";
    }
}
