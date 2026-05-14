package ae.servia.wear.watchface;

/**
 * v1.24.43 — Business Exec watch face (preset p16_business_exec).
 * Thin subclass that pins p16_business_exec as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace16BusinessExec extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p16_business_exec";
    }
}
