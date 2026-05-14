package ae.servia.wear.watchface;

import android.app.Activity;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.style.ForegroundColorSpan;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import ae.servia.wear.ServiaTheme;

/**
 * v1.24.33 — companion editor for the Servia watch face.
 *
 * Two screens, navigated by tapping the header pill:
 *
 *   1. PRESET PICKER — vertical list of the 10 curated looks.
 *      Each row shows the preset name + a colour-chip pair (theme
 *      primary + accent). Tap to apply.
 *
 *   2. SLOT EDITOR — once a preset is active, the user can override
 *      individual slots. The editor shows N rows (one per slot in
 *      the active preset) and tapping a row cycles to the next slot
 *      kind (sos_1 → sos_2 → ... → none → sos_1).
 *
 * Persistence is via {@link WatchFaceSlots}. After every change we
 * Toast a confirmation so the user knows the watch face will repaint
 * on next interactive frame.
 *
 * Future polish: live mini-preview, drag-to-reorder slot positions,
 * per-slot colour override. Out of scope for v1.
 */
public class WatchFaceEditorActivity extends Activity {

    private enum Screen { PRESET, SLOT }
    private Screen screen = Screen.PRESET;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        renderRoot();
    }

    private void renderRoot() {
        ServiaTheme theme = WatchFacePreset.byId(
            WatchFaceSlots.activePresetId(this)).theme;

        ScrollView sv = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(theme.bg);
        root.setPadding(18, 22, 18, 22);
        sv.addView(root);
        setContentView(sv);

        TextView header = new TextView(this);
        header.setText(screen == Screen.PRESET ? "🎨 PRESETS" : "⚡ SLOTS");
        header.setTextColor(theme.accent); header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 6);
        root.addView(header);

        TextView toggle = primaryBtn(
            screen == Screen.PRESET
                ? "Edit slots →"
                : "← Pick preset",
            theme.surface, theme.text);
        toggle.setOnClickListener(v -> {
            screen = (screen == Screen.PRESET) ? Screen.SLOT : Screen.PRESET;
            renderRoot();
        });
        root.addView(toggle);

        if (screen == Screen.PRESET) renderPresets(root, theme);
        else                          renderSlots(root, theme);
    }

    // ---- preset picker ------------------------------------------------

    private void renderPresets(LinearLayout root, ServiaTheme curTheme) {
        String activeId = WatchFaceSlots.activePresetId(this);
        for (WatchFacePreset p : WatchFacePreset.ALL) {
            root.addView(buildPresetRow(p, p.id.equals(activeId)));
        }
    }

    private LinearLayout buildPresetRow(WatchFacePreset p, boolean active) {
        ServiaTheme t = p.theme;
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

        // Two stacked colour chips representing primary + accent
        LinearLayout chips = new LinearLayout(this);
        chips.setOrientation(LinearLayout.VERTICAL);
        LinearLayout.LayoutParams chipsLp = new LinearLayout.LayoutParams(36, 36);
        chipsLp.rightMargin = 10;
        chips.setLayoutParams(chipsLp);
        TextView c1 = new TextView(this);
        c1.setBackgroundColor(t.primary);
        c1.setLayoutParams(new LinearLayout.LayoutParams(36, 18));
        chips.addView(c1);
        TextView c2 = new TextView(this);
        c2.setBackgroundColor(t.accent);
        c2.setLayoutParams(new LinearLayout.LayoutParams(36, 18));
        chips.addView(c2);
        card.addView(chips);

        LinearLayout meta = new LinearLayout(this);
        meta.setOrientation(LinearLayout.VERTICAL);
        meta.setLayoutParams(new LinearLayout.LayoutParams(
            0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        TextView name = new TextView(this);
        name.setText(p.name + (active ? "  ✓" : ""));
        name.setTextColor(t.text); name.setTextSize(13);
        name.setTypeface(name.getTypeface(), Typeface.BOLD);
        meta.addView(name);
        TextView sub = new TextView(this);
        sub.setText(p.layout.name().toLowerCase().replace("_", " ")
            + " · " + p.slotCount() + " slots");
        sub.setTextColor(t.textMuted); sub.setTextSize(10);
        meta.addView(sub);
        card.addView(meta);

        card.setOnClickListener(v -> {
            WatchFaceSlots.setActivePresetId(this, p.id);
            // Wipe slot overrides so preset defaults apply on next render
            for (int i = 0; i < 8; i++) WatchFaceSlots.clearSlotOverride(this, i);
            Toast.makeText(this, "Applied: " + p.name, Toast.LENGTH_SHORT).show();
            renderRoot();
        });
        return card;
    }

    // ---- slot editor --------------------------------------------------

    private void renderSlots(LinearLayout root, ServiaTheme theme) {
        WatchFacePreset p = WatchFacePreset.byId(WatchFaceSlots.activePresetId(this));

        TextView lead = new TextView(this);
        lead.setText("Tap a slot to cycle:\n" + WatchFaceSlots.KINDS.length + " kinds available");
        lead.setTextColor(theme.textMuted); lead.setTextSize(11);
        lead.setGravity(Gravity.CENTER);
        lead.setPadding(0, 8, 0, 12);
        root.addView(lead);

        for (int i = 0; i < p.slotCount(); i++) {
            root.addView(buildSlotRow(p, i, theme));
        }

        TextView reset = primaryBtn("Reset to preset defaults", 0xFF334155, 0xFFCBD5E1);
        reset.setOnClickListener(v -> {
            for (int i = 0; i < 8; i++) WatchFaceSlots.clearSlotOverride(this, i);
            Toast.makeText(this, "Slots reset", Toast.LENGTH_SHORT).show();
            renderRoot();
        });
        root.addView(reset);
    }

    private LinearLayout buildSlotRow(WatchFacePreset p, int slotIdx, ServiaTheme theme) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setBackgroundColor(theme.surface);
        card.setPadding(12, 10, 12, 10);
        card.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        clp.bottomMargin = 6;
        card.setLayoutParams(clp);
        card.setClickable(true);

        TextView idx = new TextView(this);
        idx.setText("S" + (slotIdx + 1));
        idx.setTextColor(theme.accent); idx.setTextSize(13);
        idx.setTypeface(idx.getTypeface(), Typeface.BOLD);
        LinearLayout.LayoutParams ilp = new LinearLayout.LayoutParams(40,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        ilp.rightMargin = 8;
        idx.setLayoutParams(ilp);
        card.addView(idx);

        TextView label = new TextView(this);
        String kind = WatchFaceSlots.slotKind(this, p, slotIdx);
        label.setText(WatchFaceSlots.labelFor(kind));
        label.setTextColor(theme.text); label.setTextSize(13);
        label.setLayoutParams(new LinearLayout.LayoutParams(
            0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        card.addView(label);

        card.setOnClickListener(v -> {
            String cur = WatchFaceSlots.slotKind(this, p, slotIdx);
            int next = 0;
            for (int k = 0; k < WatchFaceSlots.KINDS.length; k++) {
                if (WatchFaceSlots.KINDS[k].equals(cur)) {
                    next = (k + 1) % WatchFaceSlots.KINDS.length;
                    break;
                }
            }
            String newKind = WatchFaceSlots.KINDS[next];
            WatchFaceSlots.setSlotKind(this, slotIdx, newKind);
            label.setText(WatchFaceSlots.labelFor(newKind));
        });
        return card;
    }

    // ---- helpers ------------------------------------------------------

    private TextView primaryBtn(String text, int bg, int fg) {
        TextView b = new TextView(this);
        b.setText(text); b.setTextColor(fg); b.setTextSize(13);
        b.setBackgroundColor(bg); b.setGravity(Gravity.CENTER);
        b.setPadding(8, 12, 8, 12);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 4; lp.bottomMargin = 4;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }
}
