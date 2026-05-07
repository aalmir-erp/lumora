package ae.servia.wear;

import android.app.Activity;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.wear.tiles.TileService;

/**
 * v1.24.30 — pick one of the 10 {@link ServiaTheme}s. Listed as
 * vertically-stacked colour swatches on the watch (one per theme,
 * 56dp tall) so the customer can preview the palette at a glance and
 * tap to apply. After tapping we request a refresh of every Servia
 * tile so the new palette lands without a swipe-back.
 */
public class ThemePickerActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ServiaTheme cur = ServiaTheme.current(this);

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(cur.bg);
        root.setPadding(18, 22, 18, 22);
        sv.addView(root);
        setContentView(sv);

        TextView header = new TextView(this);
        header.setText("🎨 THEME");
        header.setTextColor(cur.accent);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 8);
        root.addView(header);

        TextView sub = new TextView(this);
        sub.setText("Tap to apply · 10 looks");
        sub.setTextColor(cur.textMuted);
        sub.setTextSize(10);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 0, 0, 12);
        root.addView(sub);

        for (ServiaTheme t : ServiaTheme.ALL) {
            root.addView(buildSwatch(t, t.id.equals(cur.id)));
        }
    }

    private LinearLayout buildSwatch(ServiaTheme t, boolean isCurrent) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setBackgroundColor(t.surface);
        card.setPadding(12, 10, 12, 10);
        card.setGravity(Gravity.CENTER_VERTICAL);

        LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        clp.bottomMargin = 6;
        card.setLayoutParams(clp);
        card.setClickable(true);

        // Coloured chip showing the primary + accent
        LinearLayout chips = new LinearLayout(this);
        chips.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams chipsLp = new LinearLayout.LayoutParams(36, 36);
        chipsLp.rightMargin = 10;
        chips.setLayoutParams(chipsLp);
        TextView primaryChip = new TextView(this);
        primaryChip.setBackgroundColor(t.primary);
        LinearLayout.LayoutParams cl1 = new LinearLayout.LayoutParams(36, 18);
        primaryChip.setLayoutParams(cl1);
        chips.addView(primaryChip);
        TextView accentChip = new TextView(this);
        accentChip.setBackgroundColor(t.accent);
        accentChip.setLayoutParams(cl1);
        chips.addView(accentChip);
        card.addView(chips);

        LinearLayout meta = new LinearLayout(this);
        meta.setOrientation(LinearLayout.VERTICAL);
        meta.setLayoutParams(new LinearLayout.LayoutParams(
            0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        TextView nm = new TextView(this);
        nm.setText(t.name + (isCurrent ? "  ✓" : ""));
        nm.setTextColor(t.text); nm.setTextSize(13);
        nm.setTypeface(nm.getTypeface(), Typeface.BOLD);
        meta.addView(nm);
        TextView tg = new TextView(this);
        tg.setText(t.tagline);
        tg.setTextColor(t.textMuted); tg.setTextSize(10);
        tg.setMaxLines(1);
        meta.addView(tg);
        card.addView(meta);

        card.setOnClickListener(v -> {
            ServiaTheme.apply(this, t.id);
            Toast.makeText(this, "Applied: " + t.name, Toast.LENGTH_SHORT).show();
            refreshAllTiles();
            recreate();
        });
        return card;
    }

    private void refreshAllTiles() {
        try {
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosQuadTileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.MySosTileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.HubTileService.class);
            TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.LocationTileService.class);
        } catch (Throwable ignored) {}
    }
}
