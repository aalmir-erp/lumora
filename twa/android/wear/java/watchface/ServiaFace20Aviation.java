package ae.servia.wear.watchface;

/**
 * v1.24.43 — Aviation watch face (preset p20_aviation).
 * Thin subclass that pins p20_aviation as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace20Aviation extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p20_aviation";
    }
}
