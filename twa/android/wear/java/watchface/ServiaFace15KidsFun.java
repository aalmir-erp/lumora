package ae.servia.wear.watchface;

/**
 * v1.24.43 — Kids Fun watch face (preset p15_kids_fun).
 * Thin subclass that pins p15_kids_fun as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace15KidsFun extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p15_kids_fun";
    }
}
