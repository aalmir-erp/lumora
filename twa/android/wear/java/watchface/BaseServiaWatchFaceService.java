package ae.servia.wear.watchface;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.res.Resources;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.SurfaceHolder;

import androidx.annotation.NonNull;
import androidx.wear.watchface.CanvasType;
import androidx.wear.watchface.ComplicationSlotsManager;
import androidx.wear.watchface.DrawMode;
import androidx.wear.watchface.ListenableWatchFaceService;
import androidx.wear.watchface.Renderer;
import androidx.wear.watchface.TapEvent;
import androidx.wear.watchface.TapType;
import androidx.wear.watchface.WatchFace;
import androidx.wear.watchface.WatchFaceType;
import androidx.wear.watchface.WatchState;
import androidx.wear.watchface.style.CurrentUserStyleRepository;
import androidx.wear.watchface.style.UserStyleSchema;

import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;

import java.time.ZonedDateTime;
import java.util.Locale;

import ae.servia.wear.WatchHomepageBridge;

/**
 * v1.24.43 — base class for all 22 Servia watch face presets.
 *
 * Each preset is its own thin subclass (ServiaFace01..ServiaFace22).
 * The subclass overrides {@link #getPresetId()} to identify itself.
 * Everything else — bitmap loading, time overlay, second-hand rotation,
 * tap-on-website handling — is shared here.
 *
 * Architecture:
 *   1. Each face has TWO bundled drawables:
 *        wf_frame_pNN   (no time text, painted as background)
 *        wf_preview_pNN (with placeholder 10:30, used as picker thumbnail)
 *      Both come from the same SVG source — see tools/watchface/.
 *   2. {@link WatchFaceRegistry} stores per-face metadata: time x/y/size/color,
 *      whether the face is analog (needs second hand), etc.
 *   3. render() draws: bitmap full-screen, then live time on top at the
 *      metadata position, then second hand (if analog), then tap-zone
 *      visual indicator at bottom for the servia.ae chip.
 *   4. onTapEvent() detects taps in the bottom servia.ae chip area and
 *      launches Chrome with https://servia.ae .
 */
public abstract class BaseServiaWatchFaceService extends ListenableWatchFaceService {

    static {
        // Idempotent: the static map only fills on first init() call.
        WatchFaceRegistry.init();
    }

    /** Subclass returns its preset id (e.g. "p1_burj_sunset"). */
    protected abstract String getPresetId();

    @NonNull
    @Override
    protected UserStyleSchema createUserStyleSchema() {
        return new UserStyleSchema(java.util.Collections.emptyList());
    }

    @NonNull
    @Override
    protected ComplicationSlotsManager createComplicationSlotsManager(
            @NonNull CurrentUserStyleRepository userStyleRepository) {
        return new ComplicationSlotsManager(
            java.util.Collections.emptyList(), userStyleRepository);
    }

    @NonNull
    @Override
    protected ListenableFuture<WatchFace> createWatchFaceFuture(
            @NonNull SurfaceHolder surfaceHolder,
            @NonNull WatchState watchState,
            @NonNull ComplicationSlotsManager complicationSlotsManager,
            @NonNull CurrentUserStyleRepository userStyleRepository) {
        ServiaRenderer renderer = new ServiaRenderer(
            surfaceHolder, this, watchState, userStyleRepository, getPresetId());
        return Futures.immediateFuture(
            new WatchFace(WatchFaceType.DIGITAL, renderer));
    }

    // ====================================================================

    private static final long FRAME_PERIOD_MS = 33L;  // ~30 fps active

    static final class ServiaRenderer extends Renderer.CanvasRenderer {

        private final Context appCtx;
        private final String presetId;
        private final WatchFaceMeta.Entry meta;

        // Cached frame bitmap so we don't decode every frame.
        private Bitmap frameBitmap;

        // Reusable paints
        private final Paint pBitmap = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        private final Paint pTime = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pSecond = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pBlack = new Paint();

        ServiaRenderer(@NonNull SurfaceHolder surfaceHolder,
                       @NonNull Context ctx,
                       @NonNull WatchState watchState,
                       @NonNull CurrentUserStyleRepository userStyleRepo,
                       @NonNull String presetId) {
            super(surfaceHolder, userStyleRepo, watchState,
                  CanvasType.HARDWARE, FRAME_PERIOD_MS,
                  /* clearWithBackgroundTintBeforeRenderingHighlightLayer */ true);
            this.appCtx = ctx.getApplicationContext();
            this.presetId = presetId;
            this.meta = WatchFaceMeta.byId(presetId);
        }

        @Override
        public void render(@NonNull Canvas canvas, @NonNull Rect bounds,
                           @NonNull ZonedDateTime now) {
            boolean ambient = getRenderParameters().getDrawMode() == DrawMode.AMBIENT;
            int w = bounds.width();
            int h = bounds.height();

            // ---- 1. background ------------------------------------------
            if (ambient) {
                pBlack.setColor(0xFF000000);
                canvas.drawRect(bounds, pBlack);
            } else {
                drawFrame(canvas, bounds);
            }

            // ---- 2. live time -------------------------------------------
            // SVG was authored on a 480-grid; scale to current surface.
            float scale = w / 480f;
            String time = String.format(Locale.US, "%02d:%02d",
                now.getHour(), now.getMinute());

            pTime.setTextAlign(Paint.Align.CENTER);
            pTime.setColor(ambient ? 0xFFFFFFFF : meta.timeColor);
            pTime.setTypeface(Typeface.create(meta.typeface(), meta.typefaceStyle()));
            pTime.setTextSize(meta.timeSize * scale);
            try {
                pTime.setLetterSpacing(meta.timeLetterSpacing / 100f);
            } catch (Throwable ignored) { /* older SDK */ }
            // Subtle drop-shadow so live time stays readable over the bitmap
            pTime.setShadowLayer(4f * scale, 0f, 2f * scale, 0x80000000);

            float tx = meta.timeX * scale;
            float ty = meta.timeY * scale;
            canvas.drawText(time, tx, ty, pTime);

            // ---- 3. second hand for analog presets ---------------------
            if (meta.hasSecondHand && !ambient) {
                drawSecondHand(canvas, bounds, now, scale);
            }
        }

        @Override
        public void renderHighlightLayer(@NonNull Canvas canvas,
                                         @NonNull Rect bounds,
                                         @NonNull ZonedDateTime zonedDateTime) {
            canvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
        }

        // ----- helpers -----------------------------------------------------

        private void drawFrame(Canvas canvas, Rect bounds) {
            if (frameBitmap == null || frameBitmap.isRecycled()) {
                try {
                    int resId = meta.resolveFrameRes(appCtx);
                    if (resId == 0) { frameBitmap = null; }
                    else {
                        BitmapFactory.Options opts = new BitmapFactory.Options();
                        opts.inPreferredConfig = Bitmap.Config.ARGB_8888;
                        frameBitmap = BitmapFactory.decodeResource(
                            appCtx.getResources(), resId, opts);
                    }
                } catch (Throwable t) {
                    frameBitmap = null;
                }
            }
            if (frameBitmap != null) {
                Rect src = new Rect(0, 0, frameBitmap.getWidth(), frameBitmap.getHeight());
                canvas.drawBitmap(frameBitmap, src, bounds, pBitmap);
            } else {
                pBlack.setColor(0xFF0F172A);
                canvas.drawRect(bounds, pBlack);
            }
        }

        private void drawSecondHand(Canvas canvas, Rect bounds,
                                     ZonedDateTime now, float scale) {
            int sec = now.getSecond();
            float angleDeg = sec * 6f - 90f;
            int cx = bounds.centerX();
            int cy = bounds.centerY();
            float length = Math.min(bounds.width(), bounds.height()) * 0.40f;
            float endX = (float) (cx + Math.cos(Math.toRadians(angleDeg)) * length);
            float endY = (float) (cy + Math.sin(Math.toRadians(angleDeg)) * length);
            pSecond.setColor(meta.timeColor);
            pSecond.setStyle(Paint.Style.STROKE);
            pSecond.setStrokeCap(Paint.Cap.ROUND);
            pSecond.setStrokeWidth(2.5f * scale);
            pSecond.setShadowLayer(3f * scale, 0f, 1.5f * scale, 0x80000000);
            canvas.drawLine(cx, cy, endX, endY, pSecond);
            // Centre pin
            pSecond.setStyle(Paint.Style.FILL);
            canvas.drawCircle(cx, cy, 5f * scale, pSecond);
        }

        // ----- tap → open servia.ae --------------------------------------

        public void onTapEvent(int tapType,
                               @NonNull TapEvent tapEvent,
                               @NonNull ComplicationSlotsManager complicationSlotsManager) {
            if (tapType != TapType.UP) return;
            // Bottom-centre 'servia.ae' chip on the frame is at y≈442 in the
            // 480 grid, with width≈116. Detect taps in roughly that band.
            SurfaceHolder sh = getSurfaceHolder();
            Rect b = sh.getSurfaceFrame();
            if (b == null || b.width() == 0) return;
            int x = tapEvent.getXPos();
            int y = tapEvent.getYPos();
            float scale = b.width() / 480f;
            float chipCx = 240f * scale;
            float chipCy = 442f * scale;
            float chipW = 130f * scale;
            float chipH = 30f * scale;
            if (Math.abs(x - chipCx) > chipW / 2f) return;
            if (Math.abs(y - chipCy) > chipH / 2f) return;
            try {
                Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse("https://servia.ae"));
                i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                appCtx.startActivity(i);
            } catch (Throwable ignored) {
                // Fallback: ping homepage bridge if present
                WatchHomepageBridge.openOnPhone(appCtx);
            }
        }
    }
}
