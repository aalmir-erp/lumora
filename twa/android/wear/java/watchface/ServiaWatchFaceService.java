package ae.servia.wear.watchface;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Build;
import android.text.format.DateFormat;
import android.view.SurfaceHolder;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
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
import java.time.format.DateTimeFormatter;
import java.util.Calendar;
import java.util.Locale;

import ae.servia.wear.ServiaTheme;

/**
 * v1.24.33 — Servia Wear OS watch face.
 *
 * One face, 10 presets. Each preset is theme + layout + slot defaults
 * (see {@link WatchFacePreset}). The user picks a preset from the
 * companion {@link WatchFaceEditorActivity} and overrides individual
 * slots there too.
 *
 * Renderer: {@link Renderer.CanvasRenderer2} draws on the canvas every
 * second in interactive mode, less often in ambient. We keep paints
 * cached per render to avoid GC churn.
 *
 * Tap handling: onTapEvent() resolves tap (x, y) to a slot index by
 * comparing against the preset's slot positions; if a hit, opens the
 * bound activity via {@link WatchFaceSlots#resolveTapAction}.
 *
 * Compile note: AndroidX watch-face Java API has long signatures and
 * a few suspending Kotlin entry points. createWatchFace is overridden
 * here as the synchronous suspendable bridge — if the build complains
 * about a missing override, double-check the watchface library version
 * and re-generate this stub from the Java sample. This file targets
 * androidx.wear.watchface 1.2.x.
 */
// ListenableWatchFaceService — Java-friendly base. The vanilla
// WatchFaceService Kotlin API uses suspending functions which make Java
// overrides impossible. ListenableWatchFaceService swaps them for
// ListenableFuture-returning equivalents that Java can return via
// Futures.immediateFuture(...). Same applies to Renderer.CanvasRenderer
// (NOT CanvasRenderer2) below.
public class ServiaWatchFaceService extends ListenableWatchFaceService {

    @NonNull
    @Override
    protected UserStyleSchema createUserStyleSchema() {
        // We manage our own preset+slot state via SharedPreferences (the
        // editor activity writes; the renderer reads). UserStyleSchema is
        // therefore empty — Wear OS doesn't need to mediate style values
        // for us. This keeps the surface area minimal.
        return new UserStyleSchema(java.util.Collections.emptyList());
    }

    @NonNull
    @Override
    protected ComplicationSlotsManager createComplicationSlotsManager(
            @NonNull CurrentUserStyleRepository userStyleRepository) {
        // Same reason as above: we draw our own slot artwork from
        // SharedPreferences. No system complications mediated through
        // the manager.
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
            surfaceHolder, this, watchState, userStyleRepository);
        return Futures.immediateFuture(
            new WatchFace(WatchFaceType.DIGITAL, renderer));
    }

    // ====================================================================
    // Renderer
    // ====================================================================

    // Default 1 fps; animated layouts request 30 fps after first frame.
    private static final long FRAME_PERIOD_STATIC_MS = 1000L;
    private static final long FRAME_PERIOD_ANIMATED_MS = 33L;  // ~30 fps

    // Renderer.CanvasRenderer (deprecated but Java-callable) instead of
    // CanvasRenderer2. The 2 variant requires overriding suspend
    // createSharedAssets() which is impossible from Java without a Kotlin
    // shim. We don't need shared assets for our render path (no large
    // bitmaps, all paints are field-cached), so the older synchronous
    // base class is the right fit here.
    static final class ServiaRenderer extends Renderer.CanvasRenderer {

        private final Context appCtx;
        // Paints reused across frames
        private final Paint pBg = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pTime = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pDate = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pSlotBg = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pSlotIcon = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pSlotLabel = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pHand = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pTick = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pBrand = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint pAmbientBg = new Paint();
        private final Paint pAmbientText = new Paint(Paint.ANTI_ALIAS_FLAG);

        ServiaRenderer(@NonNull SurfaceHolder surfaceHolder,
                       @NonNull Context ctx,
                       @NonNull WatchState watchState,
                       @NonNull CurrentUserStyleRepository userStyleRepo) {
            // 33 ms ≈ 30 fps for animated layouts. Static layouts redraw
            // every second only because the renderer skips rebuilding paint
            // state when nothing changes; not a separate constructor.
            super(surfaceHolder, userStyleRepo, watchState,
                  CanvasType.HARDWARE, FRAME_PERIOD_ANIMATED_MS,
                  /* clearWithBackgroundTintBeforeRenderingHighlightLayer */ true);
            this.appCtx = ctx.getApplicationContext();
        }

        @Override
        public void render(@NonNull Canvas canvas, @NonNull Rect bounds,
                           @NonNull ZonedDateTime zonedDateTime) {
            String presetId = WatchFaceSlots.activePresetId(appCtx);
            WatchFacePreset preset = WatchFacePreset.byId(presetId);
            ServiaTheme theme = preset.theme;
            // isAmbient() is gone in Renderer.CanvasRenderer — read DrawMode
            // from getRenderParameters() instead. Ambient mode flips the
            // bg to black + skips slot/animation drawing for battery.
            boolean ambient = getRenderParameters().getDrawMode() == DrawMode.AMBIENT;

            int w = bounds.width();
            int h = bounds.height();
            int cx = bounds.centerX();
            int cy = bounds.centerY();

            // ---- background --------------------------------------------
            if (ambient) {
                pAmbientBg.setColor(0xFF000000);
                canvas.drawRect(bounds, pAmbientBg);
            } else {
                pBg.setColor(theme.bg);
                canvas.drawRect(bounds, pBg);
            }

            // ---- layout-specific drawing -------------------------------
            long now = System.currentTimeMillis();
            switch (preset.layout) {
                case DIGITAL_LARGE: drawDigitalLarge(canvas, bounds, zonedDateTime, theme, ambient); break;
                case DIGITAL_SMALL: drawDigitalSmall(canvas, bounds, zonedDateTime, theme, ambient); break;
                case ANALOG:        drawAnalog(canvas, bounds, zonedDateTime, theme, ambient);       break;
                case HYBRID:        drawHybrid(canvas, bounds, zonedDateTime, theme, ambient);       break;
                case MINIMAL:       drawMinimal(canvas, bounds, zonedDateTime, theme, ambient);      break;
                case SANDSTORM:         drawSandstorm(canvas, bounds, zonedDateTime, theme, ambient, now); break;
                case BURJ_SKYLINE:      drawBurjSkyline(canvas, bounds, zonedDateTime, theme, ambient, now); break;
                case MARINA_PULSE:      drawMarinaPulse(canvas, bounds, zonedDateTime, theme, ambient, now); break;
                case FALCON_TRAIL:      drawFalconTrail(canvas, bounds, zonedDateTime, theme, ambient, now); break;
                case SERVICE_SPOTLIGHT: drawServiceSpotlight(canvas, bounds, zonedDateTime, theme, ambient, now, preset); break;
            }

            // ---- slots (skipped in ambient to save battery) ------------
            if (!ambient) {
                drawSlots(canvas, bounds, preset, theme);
            }

            // ---- subtle Servia brand mark in centre-top ----------------
            if (!ambient) {
                pBrand.setColor(theme.accent);
                pBrand.setTextSize(10f * w / 360f);
                pBrand.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
                pBrand.setTextAlign(Paint.Align.CENTER);
                pBrand.setLetterSpacing(0.18f);
                canvas.drawText("SERVIA", cx, h * 0.10f, pBrand);
            }
        }

        @Override
        public void renderHighlightLayer(@NonNull Canvas canvas,
                                         @NonNull Rect bounds,
                                         @NonNull ZonedDateTime zonedDateTime) {
            // Editor highlight pass — we don't override default behaviour.
            canvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
        }

        // ----- layout drawers ------------------------------------------

        private void drawDigitalLarge(Canvas c, Rect b, ZonedDateTime t,
                                       ServiaTheme theme, boolean ambient) {
            int w = b.width(), cx = b.centerX();
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());

            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            pt.setTextSize(64f * w / 360f);
            c.drawText(time, cx, b.height() * 0.40f, pt);

            if (!ambient) {
                pDate.setColor(theme.textMuted);
                pDate.setTextSize(13f * w / 360f);
                pDate.setTextAlign(Paint.Align.CENTER);
                pDate.setTypeface(Typeface.DEFAULT);
                String date = t.format(DateTimeFormatter.ofPattern("EEE d MMM",
                                                                    Locale.getDefault()));
                c.drawText(date.toUpperCase(Locale.getDefault()),
                           cx, b.height() * 0.48f, pDate);
            }
        }

        private void drawDigitalSmall(Canvas c, Rect b, ZonedDateTime t,
                                       ServiaTheme theme, boolean ambient) {
            int w = b.width(), cx = b.centerX();
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());

            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            pt.setTextSize(36f * w / 360f);
            c.drawText(time, cx, b.height() * 0.30f, pt);

            if (!ambient) {
                pDate.setColor(theme.accent);
                pDate.setTextSize(11f * w / 360f);
                pDate.setTextAlign(Paint.Align.CENTER);
                pDate.setTypeface(Typeface.DEFAULT);
                String date = t.format(DateTimeFormatter.ofPattern("EEE d MMM",
                                                                    Locale.getDefault()));
                c.drawText(date.toUpperCase(Locale.getDefault()),
                           cx, b.height() * 0.40f, pDate);
            }
        }

        private void drawAnalog(Canvas c, Rect b, ZonedDateTime t,
                                 ServiaTheme theme, boolean ambient) {
            int w = b.width(), cx = b.centerX(), cy = b.centerY();
            float r = Math.min(w, b.height()) / 2f - w * 0.05f;

            // Hour ticks
            pTick.setColor(ambient ? 0xFF888888 : theme.textMuted);
            pTick.setStrokeWidth(2f * w / 360f);
            pTick.setStyle(Paint.Style.STROKE);
            for (int i = 0; i < 12; i++) {
                double a = Math.toRadians(i * 30 - 90);
                float x1 = (float) (cx + Math.cos(a) * r);
                float y1 = (float) (cy + Math.sin(a) * r);
                float x2 = (float) (cx + Math.cos(a) * (r - w * 0.04f));
                float y2 = (float) (cy + Math.sin(a) * (r - w * 0.04f));
                c.drawLine(x1, y1, x2, y2, pTick);
            }

            // Hands
            int hr = t.getHour() % 12;
            int min = t.getMinute();
            int sec = t.getSecond();
            float hourAng = (float) Math.toRadians((hr + min / 60f) * 30 - 90);
            float minAng  = (float) Math.toRadians(min * 6 - 90);
            float secAng  = (float) Math.toRadians(sec * 6 - 90);

            pHand.setStyle(Paint.Style.STROKE);
            pHand.setStrokeCap(Paint.Cap.ROUND);

            // Hour
            pHand.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pHand.setStrokeWidth(5f * w / 360f);
            c.drawLine(cx, cy,
                (float) (cx + Math.cos(hourAng) * r * 0.55f),
                (float) (cy + Math.sin(hourAng) * r * 0.55f), pHand);
            // Minute
            pHand.setStrokeWidth(3f * w / 360f);
            c.drawLine(cx, cy,
                (float) (cx + Math.cos(minAng) * r * 0.78f),
                (float) (cy + Math.sin(minAng) * r * 0.78f), pHand);
            // Second (only in interactive)
            if (!ambient) {
                pHand.setColor(theme.accent);
                pHand.setStrokeWidth(2f * w / 360f);
                c.drawLine(cx, cy,
                    (float) (cx + Math.cos(secAng) * r * 0.85f),
                    (float) (cy + Math.sin(secAng) * r * 0.85f), pHand);
                // Centre dot
                pHand.setStyle(Paint.Style.FILL);
                pHand.setColor(theme.primary);
                c.drawCircle(cx, cy, 4f * w / 360f, pHand);
            }
        }

        private void drawHybrid(Canvas c, Rect b, ZonedDateTime t,
                                 ServiaTheme theme, boolean ambient) {
            // Analog dial + small digital readout above
            drawAnalog(c, b, t, theme, ambient);
            if (!ambient) {
                pDate.setColor(theme.accent);
                pDate.setTextSize(13f * b.width() / 360f);
                pDate.setTextAlign(Paint.Align.CENTER);
                pDate.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
                String date = t.format(DateTimeFormatter.ofPattern("d MMM",
                                                                    Locale.getDefault()));
                c.drawText(date.toUpperCase(Locale.getDefault()),
                           b.centerX(), b.height() * 0.18f, pDate);
            }
        }

        private void drawMinimal(Canvas c, Rect b, ZonedDateTime t,
                                  ServiaTheme theme, boolean ambient) {
            int w = b.width();
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());
            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create("sans-serif-thin", Typeface.NORMAL));
            pt.setTextSize(80f * w / 360f);
            c.drawText(time, b.centerX(), b.height() * 0.55f, pt);
        }

        // ----- animated layouts (v1.24.35) ------------------------------

        /** Sandstorm — drifting golden particles behind a digital time. */
        private void drawSandstorm(Canvas c, Rect b, ZonedDateTime t,
                                    ServiaTheme theme, boolean ambient, long nowMs) {
            int w = b.width(), h = b.height(), cx = b.centerX();
            // Particles
            if (!ambient) {
                pSlotIcon.setStyle(Paint.Style.FILL);
                int particleCount = 36;
                for (int i = 0; i < particleCount; i++) {
                    float seed = i * 137.5f;
                    float driftSpeed = 0.04f + (i % 5) * 0.012f;
                    float xN = ((seed + nowMs * driftSpeed * 0.001f) % 1.2f) - 0.1f;
                    float yN = (float) (0.20f + 0.60f * Math.sin((nowMs * 0.0006f + seed) * 0.5f) + 0.30f);
                    float x = b.left + xN * w;
                    float y = b.top + (yN % 1.0f) * h;
                    int alpha = 60 + (i * 15) % 120;
                    pSlotIcon.setColor((alpha << 24) | (theme.accent & 0x00FFFFFF));
                    c.drawCircle(x, y, 2.0f * w / 360f, pSlotIcon);
                }
            }
            // Time
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());
            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            pt.setTextSize(58f * w / 360f);
            c.drawText(time, cx, h * 0.45f, pt);
            if (!ambient) {
                pDate.setColor(theme.accent);
                pDate.setTextSize(11f * w / 360f);
                pDate.setTextAlign(Paint.Align.CENTER);
                pDate.setLetterSpacing(0.18f);
                c.drawText("AC SEASON · BOOK NOW", cx, h * 0.55f, pDate);
            }
        }

        /** Burj Skyline — silhouette + twinkling lights against the night. */
        private void drawBurjSkyline(Canvas c, Rect b, ZonedDateTime t,
                                      ServiaTheme theme, boolean ambient, long nowMs) {
            int w = b.width(), h = b.height(), cx = b.centerX();
            // Sky gradient (we fake it with two filled rects since LinearGradient
            // would mean caching a Shader; keep it allocation-free).
            // Skyline silhouette — five buildings + Burj-tall centre spire.
            pHand.setStyle(Paint.Style.FILL);
            pHand.setColor(0xFF0F172A);
            float baseY = h * 0.72f;
            // Building rectangles
            float[] heights = {0.20f, 0.32f, 0.55f, 0.32f, 0.22f};
            float[] widths  = {0.16f, 0.13f, 0.18f, 0.13f, 0.16f};
            float xCursor = w * 0.05f;
            for (int i = 0; i < heights.length; i++) {
                float bw = w * widths[i];
                float bh = h * heights[i];
                c.drawRect(b.left + xCursor, baseY - bh,
                           b.left + xCursor + bw, baseY, pHand);
                xCursor += bw + w * 0.005f;
            }
            // Burj spire from centre tower
            pHand.setStrokeWidth(3f * w / 360f);
            pHand.setStyle(Paint.Style.FILL);
            float spireBaseX = b.left + w * 0.50f;
            float spireBaseY = baseY - h * 0.55f;
            android.graphics.Path spire = new android.graphics.Path();
            spire.moveTo(spireBaseX - w * 0.02f, spireBaseY);
            spire.lineTo(spireBaseX + w * 0.02f, spireBaseY);
            spire.lineTo(spireBaseX, spireBaseY - h * 0.12f);
            spire.close();
            c.drawPath(spire, pHand);

            // Twinkling lights
            if (!ambient) {
                pSlotIcon.setStyle(Paint.Style.FILL);
                long phase = nowMs / 200L;
                for (int i = 0; i < 16; i++) {
                    float lx = b.left + w * (0.10f + (i * 0.055f));
                    float ly = baseY - h * (0.05f + ((i * 7 + phase) % 12) * 0.03f);
                    int twinkle = (int) ((Math.sin((nowMs + i * 233) * 0.005) + 1.0) * 110);
                    pSlotIcon.setColor((twinkle << 24) | (theme.accent & 0x00FFFFFF));
                    c.drawCircle(lx, ly, 1.6f * w / 360f, pSlotIcon);
                }
            }

            // Time
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());
            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            pt.setTextSize(48f * w / 360f);
            c.drawText(time, cx, h * 0.30f, pt);
        }

        /** Marina Pulse — water ripple expanding from centre on each second. */
        private void drawMarinaPulse(Canvas c, Rect b, ZonedDateTime t,
                                      ServiaTheme theme, boolean ambient, long nowMs) {
            int w = b.width(), h = b.height(), cx = b.centerX(), cy = b.centerY();
            if (!ambient) {
                // Three ripples staggered by 333ms each, expanding 0->1 over 1s
                pHand.setStyle(Paint.Style.STROKE);
                for (int i = 0; i < 3; i++) {
                    float phase = ((nowMs + i * 333L) % 1000L) / 1000f;
                    float r = phase * Math.min(w, h) * 0.45f;
                    int alpha = (int) ((1f - phase) * 140);
                    pHand.setColor((alpha << 24) | (theme.accent & 0x00FFFFFF));
                    pHand.setStrokeWidth((1f - phase) * 4f * w / 360f + 1f);
                    c.drawCircle(cx, cy, r, pHand);
                }
            }
            // Time
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());
            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create("sans-serif-light", Typeface.NORMAL));
            pt.setTextSize(54f * w / 360f);
            c.drawText(time, cx, cy + h * 0.05f, pt);
            if (!ambient) {
                pDate.setColor(theme.accent);
                pDate.setTextSize(10f * w / 360f);
                pDate.setTextAlign(Paint.Align.CENTER);
                pDate.setLetterSpacing(0.18f);
                c.drawText("DUBAI MARINA", cx, h * 0.62f, pDate);
            }
        }

        /** Falcon Trail — a UAE falcon emoji orbits the time. */
        private void drawFalconTrail(Canvas c, Rect b, ZonedDateTime t,
                                      ServiaTheme theme, boolean ambient, long nowMs) {
            int w = b.width(), h = b.height(), cx = b.centerX(), cy = b.centerY();
            // Time at centre
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());
            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            pt.setTextSize(56f * w / 360f);
            c.drawText(time, cx, cy + h * 0.05f, pt);

            if (!ambient) {
                // Trail of fading dots behind the falcon
                pSlotIcon.setStyle(Paint.Style.FILL);
                double angBase = (nowMs % 3500L) / 3500.0 * 2 * Math.PI - Math.PI / 2;
                float r = Math.min(w, h) * 0.36f;
                for (int i = 0; i < 8; i++) {
                    double a = angBase - i * 0.12;
                    float tx = (float) (cx + Math.cos(a) * r);
                    float ty = (float) (cy + Math.sin(a) * r);
                    int alpha = 200 - i * 22;
                    if (alpha < 30) alpha = 30;
                    pSlotIcon.setColor((alpha << 24) | (theme.accent & 0x00FFFFFF));
                    c.drawCircle(tx, ty, (8f - i) * w / 360f, pSlotIcon);
                }
                // Falcon glyph
                float fx = (float) (cx + Math.cos(angBase) * r);
                float fy = (float) (cy + Math.sin(angBase) * r);
                pSlotIcon.setColor(0xFFFFFFFF);
                pSlotIcon.setTextAlign(Paint.Align.CENTER);
                pSlotIcon.setTextSize(20f * w / 360f);
                c.drawText("🦅", fx, fy + 6f * w / 360f, pSlotIcon);
            }
        }

        /** Service Spotlight — rotating beam highlights one slot at a time. */
        private void drawServiceSpotlight(Canvas c, Rect b, ZonedDateTime t,
                                            ServiaTheme theme, boolean ambient,
                                            long nowMs, WatchFacePreset preset) {
            int w = b.width(), h = b.height(), cx = b.centerX(), cy = b.centerY();
            // Time at top
            String time = String.format(Locale.US, "%02d:%02d",
                t.getHour(), t.getMinute());
            Paint pt = ambient ? pAmbientText : pTime;
            pt.setColor(ambient ? 0xFFFFFFFF : theme.text);
            pt.setTextAlign(Paint.Align.CENTER);
            pt.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            pt.setTextSize(46f * w / 360f);
            c.drawText(time, cx, h * 0.30f, pt);

            if (!ambient) {
                // Rotate a soft cone through the corners at one slot every 2s
                int n = preset.slotCount();
                int idx = (int) ((nowMs / 2000L) % n);
                float[] pos = preset.slotPosition(idx);
                float sx = b.left + pos[0] * w;
                float sy = b.top + pos[1] * h;
                // Faint gradient-like cone faked as a pile of decreasing-alpha
                // discs from centre to slot
                pSlotIcon.setStyle(Paint.Style.FILL);
                for (int i = 0; i < 12; i++) {
                    float ratio = i / 12f;
                    float x = cx + (sx - cx) * ratio;
                    float y = cy + (sy - cy) * ratio;
                    int alpha = (int) ((1f - ratio) * 70);
                    pSlotIcon.setColor((alpha << 24) | (theme.accent & 0x00FFFFFF));
                    c.drawCircle(x, y, 14f * w / 360f * (1f - ratio * 0.4f), pSlotIcon);
                }
            }
        }

        // ----- slots ----------------------------------------------------

        private void drawSlots(Canvas c, Rect b, WatchFacePreset preset,
                                ServiaTheme theme) {
            int n = preset.slotCount();
            float r = preset.slotRadiusFraction() * Math.min(b.width(), b.height());
            for (int i = 0; i < n; i++) {
                float[] pos = preset.slotPosition(i);
                float x = b.left + pos[0] * b.width();
                float y = b.top + pos[1] * b.height();
                String kind = WatchFaceSlots.slotKind(appCtx, preset, i);
                drawSlot(c, x, y, r, kind, theme);
            }
        }

        private void drawSlot(Canvas c, float x, float y, float r,
                              String kind, ServiaTheme theme) {
            // Empty slot: faint outlined circle
            if (kind == null || "none".equals(kind)) {
                pSlotBg.setStyle(Paint.Style.STROKE);
                pSlotBg.setColor(theme.dividerArgb);
                pSlotBg.setStrokeWidth(1.5f);
                c.drawCircle(x, y, r, pSlotBg);
                return;
            }

            int slotBg, slotFg;
            if (kind.startsWith("sos_")) {
                slotBg = 0xFFDC2626; slotFg = 0xFFFFFFFF;
            } else if (kind.equals("talk")) {
                slotBg = 0xFFF59E0B; slotFg = 0xFF1E293B;
            } else if (kind.equals("nfc")) {
                slotBg = 0xFF6366F1; slotFg = 0xFFFFFFFF;
            } else if (kind.equals("book") || kind.equals("track")) {
                slotBg = theme.primary; slotFg = theme.text;
            } else if (kind.equals("next_booking")) {
                slotBg = theme.accent; slotFg = 0xFF1E293B;
            } else {
                slotBg = theme.surface; slotFg = theme.text;
            }

            pSlotBg.setStyle(Paint.Style.FILL);
            pSlotBg.setColor(slotBg);
            c.drawCircle(x, y, r, pSlotBg);

            // v1.24.35 — booking-aware data slots. next_booking shows the
            // ETA in minutes pulled from SharedPreferences populated by
            // WearMessageListenerService when the server pushes
            // /servia/booking_created.
            if ("next_booking".equals(kind)) {
                android.content.SharedPreferences sp = appCtx
                    .getSharedPreferences("servia_next_booking", Context.MODE_PRIVATE);
                int etaMin = sp.getInt("eta_min", 0);
                if (etaMin > 0) {
                    pSlotIcon.setColor(slotFg);
                    pSlotIcon.setTextAlign(Paint.Align.CENTER);
                    pSlotIcon.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
                    pSlotIcon.setTextSize(r * 0.55f);
                    c.drawText(etaMin + "m", x, y - r * 0.05f, pSlotIcon);
                    pSlotIcon.setTextSize(r * 0.32f);
                    pSlotIcon.setTypeface(Typeface.DEFAULT);
                    String svc = sp.getString("service", "");
                    if (svc.length() > 6) svc = svc.substring(0, 6);
                    c.drawText(svc, x, y + r * 0.42f, pSlotIcon);
                    return;
                }
            }

            // Default: emoji from label
            pSlotIcon.setColor(slotFg);
            pSlotIcon.setTextAlign(Paint.Align.CENTER);
            pSlotIcon.setTypeface(Typeface.DEFAULT);
            pSlotIcon.setTextSize(r * 0.95f);
            String icon = WatchFaceSlots.labelFor(kind);
            int firstCp = icon.codePointAt(0);
            String iconStr = new String(Character.toChars(firstCp));
            c.drawText(iconStr, x, y + r * 0.30f, pSlotIcon);
        }

        // ----- tap ------------------------------------------------------

        // @TapType.TapType is the nested IntDef annotation on
        // androidx.wear.watchface.TapType; the outer TapType is a class
        // holding the int constants (DOWN=0, UP=1, CANCEL=2). Easy to
        // confuse — javac said "TapType cannot be converted to Annotation"
        // when we used the outer name as the annotation.
        @Override
        public void onTapEvent(@TapType.TapType int tapType,
                               @NonNull TapEvent tapEvent,
                               @NonNull ComplicationSlotsManager complicationSlotsManager) {
            // Renderer.CanvasRenderer.onTapEvent has no super impl that's
            // safe to call from Java (the open Kotlin variant is sketchy
            // through bytecode), so we just override and skip super.
            if (tapType != TapType.UP) return;
            int x = tapEvent.getXPos();
            int y = tapEvent.getYPos();
            // Use the screen bounds we last drew with — Renderer.getScreenBounds
            // would be ideal but isn't reliably exposed across versions; we
            // re-fetch from surface holder.
            SurfaceHolder sh = getSurfaceHolder();
            Rect b = sh.getSurfaceFrame();
            if (b == null || b.width() == 0) return;

            String presetId = WatchFaceSlots.activePresetId(appCtx);
            WatchFacePreset preset = WatchFacePreset.byId(presetId);
            int n = preset.slotCount();
            float r = preset.slotRadiusFraction() * Math.min(b.width(), b.height());
            for (int i = 0; i < n; i++) {
                float[] pos = preset.slotPosition(i);
                float sx = b.left + pos[0] * b.width();
                float sy = b.top + pos[1] * b.height();
                float dx = x - sx, dy = y - sy;
                if (dx * dx + dy * dy > r * r * 1.4f) continue;  // generous hit area
                String kind = WatchFaceSlots.slotKind(appCtx, preset, i);
                String[] action = WatchFaceSlots.resolveTapAction(kind);
                if (action == null) return;
                try {
                    Intent intent = new Intent();
                    intent.setComponent(new ComponentName("ae.servia.wear", action[0]));
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    if (action[1] != null) {
                        try { intent.putExtra("slot", Integer.parseInt(action[1])); }
                        catch (NumberFormatException ignored) {}
                    }
                    appCtx.startActivity(intent);
                } catch (Throwable ignored) { /* swallow — face must keep drawing */ }
                return;
            }
        }
    }

}
