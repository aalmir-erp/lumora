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
import androidx.wear.watchface.Renderer;
import androidx.wear.watchface.TapEvent;
import androidx.wear.watchface.TapType;
import androidx.wear.watchface.WatchFace;
import androidx.wear.watchface.WatchFaceService;
import androidx.wear.watchface.WatchFaceType;
import androidx.wear.watchface.WatchState;
import androidx.wear.watchface.style.CurrentUserStyleRepository;
import androidx.wear.watchface.style.UserStyleSchema;

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
public class ServiaWatchFaceService extends WatchFaceService {

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
    protected WatchFace createWatchFace(
            @NonNull SurfaceHolder surfaceHolder,
            @NonNull WatchState watchState,
            @NonNull ComplicationSlotsManager complicationSlotsManager,
            @NonNull CurrentUserStyleRepository userStyleRepository) {
        ServiaRenderer renderer = new ServiaRenderer(
            surfaceHolder, this, watchState, userStyleRepository);
        return new WatchFace(WatchFaceType.DIGITAL, renderer);
    }

    // ====================================================================
    // Renderer
    // ====================================================================

    private static final long FRAME_PERIOD_MS = 1000L;  // 1 fps in interactive

    static final class ServiaRenderer
            extends Renderer.CanvasRenderer2<ServiaSharedAssets> {

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
            super(surfaceHolder, userStyleRepo, watchState,
                  CanvasType.HARDWARE, FRAME_PERIOD_MS,
                  /* clearWithBackgroundTintBeforeRenderingHighlightLayer */ true);
            this.appCtx = ctx.getApplicationContext();
        }

        @NonNull
        @Override
        public ServiaSharedAssets createSharedAssets() {
            return new ServiaSharedAssets();
        }

        @Override
        public void render(@NonNull Canvas canvas, @NonNull Rect bounds,
                           @NonNull ZonedDateTime zonedDateTime,
                           @NonNull ServiaSharedAssets shared) {
            String presetId = WatchFaceSlots.activePresetId(appCtx);
            WatchFacePreset preset = WatchFacePreset.byId(presetId);
            ServiaTheme theme = preset.theme;
            boolean ambient = isAmbient();

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
            switch (preset.layout) {
                case DIGITAL_LARGE: drawDigitalLarge(canvas, bounds, zonedDateTime, theme, ambient); break;
                case DIGITAL_SMALL: drawDigitalSmall(canvas, bounds, zonedDateTime, theme, ambient); break;
                case ANALOG:        drawAnalog(canvas, bounds, zonedDateTime, theme, ambient);       break;
                case HYBRID:        drawHybrid(canvas, bounds, zonedDateTime, theme, ambient);       break;
                case MINIMAL:       drawMinimal(canvas, bounds, zonedDateTime, theme, ambient);      break;
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
                                         @NonNull ZonedDateTime zonedDateTime,
                                         @NonNull ServiaSharedAssets shared) {
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
            } else if (kind.equals("book") || kind.equals("track")) {
                slotBg = theme.primary; slotFg = theme.text;
            } else {
                slotBg = theme.surface; slotFg = theme.text;
            }

            pSlotBg.setStyle(Paint.Style.FILL);
            pSlotBg.setColor(slotBg);
            c.drawCircle(x, y, r, pSlotBg);

            // Icon (emoji from label) — we draw the first character of the
            // human-readable label since the watch face renderer can't pull
            // bitmaps from R.drawable for every kind without bloat.
            pSlotIcon.setColor(slotFg);
            pSlotIcon.setTextAlign(Paint.Align.CENTER);
            pSlotIcon.setTypeface(Typeface.DEFAULT);
            pSlotIcon.setTextSize(r * 0.95f);
            String icon = WatchFaceSlots.labelFor(kind);
            // First codepoint = the emoji
            int firstCp = icon.codePointAt(0);
            String iconStr = new String(Character.toChars(firstCp));
            c.drawText(iconStr, x, y + r * 0.30f, pSlotIcon);
        }

        // ----- tap ------------------------------------------------------

        @Override
        public void onTapEvent(@TapType.TapType int tapType,
                               @NonNull TapEvent tapEvent,
                               @Nullable ComplicationSlotsManager complicationSlotsManager) {
            super.onTapEvent(tapType, tapEvent, complicationSlotsManager);
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

    /** Empty asset bag — required by Renderer.CanvasRenderer2 generic. */
    static final class ServiaSharedAssets implements Renderer.SharedAssets {
        @Override public void onDestroy() {}
    }
}
