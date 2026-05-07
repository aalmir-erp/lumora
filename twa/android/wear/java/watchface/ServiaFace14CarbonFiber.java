package ae.servia.wear.watchface;

/**
 * v1.24.43 — Carbon Fiber watch face (preset p14_carbon_fiber).
 * Thin subclass that pins p14_carbon_fiber as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace14CarbonFiber extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p14_carbon_fiber";
    }
}
