package ae.servia.wear.watchface;

/**
 * v1.24.43 — Pearl Ladies watch face (preset p9_pearl_ladies).
 * Thin subclass that pins p9_pearl_ladies as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace09PearlLadies extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p9_pearl_ladies";
    }
}
