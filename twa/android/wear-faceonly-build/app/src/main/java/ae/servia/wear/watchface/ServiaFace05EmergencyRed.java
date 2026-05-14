package ae.servia.wear.watchface;

/**
 * v1.24.43 — Emergency Red watch face (preset p5_emergency_red).
 * Thin subclass that pins p5_emergency_red as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace05EmergencyRed extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p5_emergency_red";
    }
}
