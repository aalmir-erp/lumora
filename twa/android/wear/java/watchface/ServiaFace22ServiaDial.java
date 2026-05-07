package ae.servia.wear.watchface;

/**
 * v1.24.43 — Servia Dial watch face (preset p22_servia_dial).
 * Thin subclass that pins p22_servia_dial as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace22ServiaDial extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p22_servia_dial";
    }
}
