package ae.servia.wear.watchface;

/**
 * v1.24.43 — Pixel Retro watch face (preset p13_pixel_retro).
 * Thin subclass that pins p13_pixel_retro as its preset; the renderer logic lives
 * in {@link BaseServiaWatchFaceService}.
 */
public class ServiaFace13PixelRetro extends BaseServiaWatchFaceService {
    @Override
    protected String getPresetId() {
        return "p13_pixel_retro";
    }
}
