package ae.servia.wear.watchface;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.Rect;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.service.wallpaper.WallpaperService;
import android.view.MotionEvent;
import android.view.SurfaceHolder;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * v1.24.52 — PLAN B: legacy WallpaperService-based watch face.
 *
 * Diagnostic showed Samsung One UI Watch picker on Wear OS 6 enumerates
 * all 22 of our AndroidX-based watch face services via queryIntentServices
 * but FILTERS them out of the visible picker UI. Hypothesis: Samsung's
 * picker has a class-hierarchy filter that excludes services extending
 * androidx.wear.watchface.* (modern AndroidX faces) but accepts services
 * extending android.service.wallpaper.WallpaperService directly (legacy
 * path — same as Samsung's own com.google.android.clockwork.sysui.
 * experiences.defaultwatchface.DefaultWatchFace).
 *
 * This class tests that hypothesis by extending WallpaperService directly
 * with NO AndroidX dependency. Renders Burj Sunset (preset 1).
 *
 * If this one appears in the picker after install while the 22 AndroidX
 * ones still don't, we expand to all 22. If it ALSO doesn't appear, the
 * filter is on installation source (Play Store vs sideload) — only Play
 * Store internal testing or Samsung Galaxy Store is the path forward.
 *
 * Implementation notes:
 *   - Engine.onCreate loads the wf_frame_p01 PNG from drawable
 *   - Engine renders at 1 fps via a Handler post + 1000ms delay
 *   - Live time at the SVG-authored coordinates (480-grid) scaled to
 *     surface width
 *   - Tap on bottom 'servia.ae' chip area opens the website
 *   - DELIBERATELY NO WFF property metadata — matches Samsung's
 *     DefaultWatchFace which is also pure-legacy with no WFF marker.
 */
public class LegacyServiaFace01 extends WallpaperService {

    @Override
    public Engine onCreateEngine() {
        return new ServiaEngine();
    }

    private class ServiaEngine extends Engine {

        private final Handler handler = new Handler(Looper.getMainLooper());
        private boolean visible;
        private Bitmap frameBitmap;
        private final Paint timePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint bgPaint = new Paint();

        // Per-face metadata from tools-metadata.json for p1_burj_sunset
        // (text x/y/size/color baked in so we don't depend on the
        // WatchFaceMeta registry — keep this class fully self-contained).
        private static final float TIME_X = 240f;
        private static final float TIME_Y = 190f;
        private static final int   TIME_SIZE = 92;
        private static final int   TIME_COLOR = 0xFFFFFFFF;
        // SVG canvas was 480; scale to actual surface width.

        private final Runnable tick = new Runnable() {
            @Override public void run() {
                draw();
                if (visible) handler.postDelayed(this, 1000L);
            }
        };

        @Override
        public void onCreate(SurfaceHolder holder) {
            super.onCreate(holder);
            setTouchEventsEnabled(true);
            try {
                int resId = getResources().getIdentifier(
                    "wf_frame_p01", "drawable", getPackageName());
                if (resId != 0) {
                    BitmapFactory.Options opts = new BitmapFactory.Options();
                    opts.inPreferredConfig = Bitmap.Config.ARGB_8888;
                    frameBitmap = BitmapFactory.decodeResource(
                        getResources(), resId, opts);
                }
            } catch (Throwable ignored) {}

            timePaint.setColor(TIME_COLOR);
            timePaint.setTextAlign(Paint.Align.CENTER);
            timePaint.setTypeface(Typeface.create(Typeface.SERIF, Typeface.BOLD));
            timePaint.setShadowLayer(4f, 0f, 2f, 0x80000000);
        }

        @Override
        public void onVisibilityChanged(boolean v) {
            visible = v;
            handler.removeCallbacks(tick);
            if (v) handler.post(tick);
        }

        @Override
        public void onSurfaceRedrawNeeded(SurfaceHolder holder) {
            draw();
        }

        @Override
        public void onSurfaceChanged(SurfaceHolder holder, int format,
                                      int width, int height) {
            super.onSurfaceChanged(holder, format, width, height);
            draw();
        }

        @Override
        public void onTouchEvent(MotionEvent e) {
            if (e.getAction() != MotionEvent.ACTION_UP) return;
            // servia.ae chip lives at the bottom of the 480-grid SVG,
            // at roughly y=442 with width 130. Convert to actual coords.
            SurfaceHolder h = getSurfaceHolder();
            Rect b = h.getSurfaceFrame();
            if (b == null || b.width() == 0) return;
            float scale = b.width() / 480f;
            float chipCx = 240f * scale;
            float chipCy = 442f * scale;
            float chipW = 130f * scale;
            float chipH = 30f * scale;
            float x = e.getX(), y = e.getY();
            if (Math.abs(x - chipCx) > chipW / 2f) return;
            if (Math.abs(y - chipCy) > chipH / 2f) return;
            try {
                Intent i = new Intent(Intent.ACTION_VIEW,
                                       Uri.parse("https://servia.ae"));
                i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getApplicationContext().startActivity(i);
            } catch (Throwable ignored) {}
        }

        @Override
        public void onDestroy() {
            handler.removeCallbacks(tick);
            if (frameBitmap != null && !frameBitmap.isRecycled()) {
                frameBitmap.recycle();
                frameBitmap = null;
            }
            super.onDestroy();
        }

        private void draw() {
            SurfaceHolder holder = getSurfaceHolder();
            Canvas canvas = null;
            try {
                canvas = holder.lockCanvas();
                if (canvas == null) return;
                int w = canvas.getWidth();
                int h = canvas.getHeight();

                // Background: frame bitmap stretched to fit
                if (frameBitmap != null && !frameBitmap.isRecycled()) {
                    Rect src = new Rect(0, 0, frameBitmap.getWidth(),
                                                frameBitmap.getHeight());
                    Rect dst = new Rect(0, 0, w, h);
                    canvas.drawBitmap(frameBitmap, src, dst, null);
                } else {
                    canvas.drawColor(0xFF0F172A, PorterDuff.Mode.SRC);
                }

                // Live time on top
                float scale = w / 480f;
                timePaint.setTextSize(TIME_SIZE * scale);
                String time = new SimpleDateFormat("HH:mm", Locale.US)
                    .format(new Date());
                canvas.drawText(time, TIME_X * scale, TIME_Y * scale, timePaint);
            } catch (Throwable ignored) {
                // Surface might be released mid-draw
            } finally {
                if (canvas != null) {
                    try { holder.unlockCanvasAndPost(canvas); }
                    catch (Throwable ignored) {}
                }
            }
        }
    }
}
