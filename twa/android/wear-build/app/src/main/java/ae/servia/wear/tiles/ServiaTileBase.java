package ae.servia.wear.tiles;

import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.protolayout.TimelineBuilders;
import androidx.wear.protolayout.ResourceBuilders;
import androidx.wear.tiles.RequestBuilders;
import androidx.wear.tiles.TileBuilders;
import androidx.wear.tiles.TileService;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;

/**
 * Shared base for all Servia tile services. Each subclass overrides
 * buildLayout() to return its own ProtoLayout. We handle the common
 * boilerplate (resources, timeline wrapping, version string) here so
 * each tile is ~30-50 lines instead of 100.
 */
public abstract class ServiaTileBase extends TileService {

    /** Tile colour palette — Servia teal + amber accent */
    protected static final int TEAL = 0xFF0F766E;
    protected static final int TEAL_LIGHT = 0xFF14B8A6;
    protected static final int AMBER = 0xFFFCD34D;
    protected static final int AMBER_DEEP = 0xFFF59E0B;
    protected static final int RED = 0xFFDC2626;
    protected static final int DARK = 0xFF0F172A;
    protected static final int WHITE = 0xFFFFFFFF;

    protected static final String RESOURCES_VERSION = "1";

    @Override
    protected ListenableFuture<TileBuilders.Tile> onTileRequest(
            RequestBuilders.TileRequest req) {
        TileBuilders.Tile tile = new TileBuilders.Tile.Builder()
            .setResourcesVersion(RESOURCES_VERSION)
            .setTileTimeline(
                new TimelineBuilders.Timeline.Builder()
                    .addTimelineEntry(
                        new TimelineBuilders.TimelineEntry.Builder()
                            .setLayout(
                                new LayoutElementBuilders.Layout.Builder()
                                    .setRoot(buildLayout(req))
                                    .build())
                            .build())
                    .build())
            .setFreshnessIntervalMillis(60 * 60 * 1000L)  // 1 hr refresh
            .build();
        return Futures.immediateFuture(tile);
    }

    @Override
    protected ListenableFuture<ResourceBuilders.Resources> onTileResourcesRequest(
            RequestBuilders.ResourcesRequest req) {
        return Futures.immediateFuture(
            new ResourceBuilders.Resources.Builder()
                .setVersion(RESOURCES_VERSION)
                .build());
    }

    /** Subclasses build their own ProtoLayout root. */
    protected abstract LayoutElementBuilders.LayoutElement buildLayout(
            RequestBuilders.TileRequest req);

    // ---- Convenience builders so each tile reads cleanly --------------

    protected LayoutElementBuilders.Text title(String text, int color) {
        return new LayoutElementBuilders.Text.Builder()
            .setText(text)
            .setFontStyle(
                new LayoutElementBuilders.FontStyle.Builder()
                    .setSize(DimensionBuilders.sp(13))
                    .setWeight(LayoutElementBuilders.FONT_WEIGHT_BOLD)
                    .setColor(ColorBuilders.argb(color))
                    .build())
            .setMaxLines(1)
            .build();
    }

    protected LayoutElementBuilders.Text big(String text, int color) {
        return new LayoutElementBuilders.Text.Builder()
            .setText(text)
            .setFontStyle(
                new LayoutElementBuilders.FontStyle.Builder()
                    .setSize(DimensionBuilders.sp(28))
                    .setWeight(LayoutElementBuilders.FONT_WEIGHT_BOLD)
                    .setColor(ColorBuilders.argb(color))
                    .build())
            .setMaxLines(1)
            .build();
    }

    protected LayoutElementBuilders.Text body(String text, int color) {
        return new LayoutElementBuilders.Text.Builder()
            .setText(text)
            .setFontStyle(
                new LayoutElementBuilders.FontStyle.Builder()
                    .setSize(DimensionBuilders.sp(11))
                    .setColor(ColorBuilders.argb(color))
                    .build())
            .setMaxLines(3)
            .build();
    }

    /** A solid-color rounded box wrapper. */
    protected LayoutElementBuilders.Box wrap(int bgColor,
            LayoutElementBuilders.LayoutElement child) {
        return new LayoutElementBuilders.Box.Builder()
            .setWidth(DimensionBuilders.expand())
            .setHeight(DimensionBuilders.expand())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
            .setModifiers(
                new ModifiersBuilders.Modifiers.Builder()
                    .setBackground(
                        new ModifiersBuilders.Background.Builder()
                            .setColor(ColorBuilders.argb(bgColor))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(20))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(12))
                            .build())
                    .build())
            .addContent(child)
            .build();
    }

    /** Vertical column container. */
    protected LayoutElementBuilders.Column.Builder col() {
        return new LayoutElementBuilders.Column.Builder()
            .setWidth(DimensionBuilders.expand())
            .setHeight(DimensionBuilders.wrap())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER);
    }

    /** Spacer with given dp height. */
    protected LayoutElementBuilders.Spacer spacer(int dp) {
        return new LayoutElementBuilders.Spacer.Builder()
            .setHeight(DimensionBuilders.dp(dp))
            .build();
    }
}
