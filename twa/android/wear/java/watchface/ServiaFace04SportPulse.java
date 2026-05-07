package ae.servia.wear.watchface;

/**
 * v1.24.43 — Sport Pulse watch face (preset p4_sport_pulse).
 * Thin subclass that pins p4_sport_pulse as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace04SportPulse extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p4_sport_pulse";
    }
}
