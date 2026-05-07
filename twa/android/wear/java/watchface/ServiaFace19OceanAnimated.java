package ae.servia.wear.watchface;

/**
 * v1.24.43 — Ocean Live watch face (preset p19_ocean_animated).
 * Thin subclass that pins p19_ocean_animated as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace19OceanAnimated extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p19_ocean_animated";
    }
}
