package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * "🎯 My Servia SOS" wear activity (v1.24.15).
 *
 * Fetches /api/sos/custom/me → renders the customer's saved one-tap
 * shortcuts as scrollable cards. Tapping a card POSTs to
 * /api/sos/custom/{id}/dispatch and renders the vendor card.
 *
 * If the shortcut is pin_required, prompts a PIN entry sheet first.
 *
 * Empty state: "No shortcuts yet — open Servia on your phone to create
 * one." (per spec).
 */
public class MySosActivity extends Activity {

    private LinearLayout root;
    private ProgressBar spinner;
    private TextView statusView;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", MySosActivity.class.getName());
            startActivity(onb); finish(); return;
        }

        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(10, 18, 10, 12);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("🎯 MY SERVIA SOS");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 6);
        root.addView(header);

        spinner = new ProgressBar(this);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(36, 36);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setTextColor(0xFFCBD5E1);
        statusView.setTextSize(11);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 6, 0, 6);
        root.addView(statusView);

        loadShortcuts();
    }

    private void loadShortcuts() {
        statusView.setText("Loading your shortcuts…");
        bg.submit(() -> {
            try {
                URL u = new URL("https://servia.ae/api/sos/custom/me");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestProperty("Authorization", "Bearer " + WearAuth.getToken(this));
                con.setConnectTimeout(8000);
                con.setReadTimeout(12000);
                con.setRequestProperty("User-Agent", "ServiaWear/1.24.41 (Android Wear OS)");
                int code = con.getResponseCode();
                BufferedReader r = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line; while ((line = r.readLine()) != null) sb.append(line);
                r.close();
                if (code >= 200 && code < 300) {
                    JSONObject j = new JSONObject(sb.toString());
                    JSONArray items = j.optJSONArray("items");
                    ui.post(() -> renderList(items));
                } else {
                    ui.post(() -> statusView.setText("⚠ HTTP " + code + ": " + sb));
                }
            } catch (Exception e) {
                ui.post(() -> statusView.setText("⚠ " + (e.getMessage() == null ? "Network error" : e.getMessage())));
            }
        });
    }

    private void renderList(JSONArray items) {
        spinner.setVisibility(View.GONE);

        // v1.24.29 — "+ Create new" card always shown at top so the watch
        // is no longer dependent on the phone for shortcut creation.
        addCreateCard();

        // v1.24.31 — auto-bind the top 4 server-side custom shortcuts to
        // slots 1..4 so the QuadTile stays in sync without any phone-side
        // native code. User manual binds (from CustomSosCreateActivity's
        // slot picker) override on next save. This makes phone-created
        // shortcuts appear on the watch face after one MySosActivity open.
        autoBindSlots(items);

        if (items == null || items.length() == 0) {
            statusView.setText("No shortcuts yet.\nTap ➕ above to create.");
            statusView.setTextColor(0xFFFCD34D);
            statusView.setTextSize(13);
            return;
        }
        statusView.setText(items.length() + " shortcut" + (items.length() == 1 ? "" : "s"));
        for (int i = 0; i < items.length(); i++) {
            JSONObject b = items.optJSONObject(i);
            if (b == null) continue;
            addCard(b);
        }
        // Footer tip
        TextView tip = new TextView(this);
        tip.setText("Pin individual shortcuts\nto watch face: long-press\nface → Tiles → Slot 1-5");
        tip.setTextColor(0xFF64748B);
        tip.setTextSize(10);
        tip.setGravity(Gravity.CENTER);
        tip.setPadding(0, 12, 0, 0);
        root.addView(tip);
    }

    /** v1.24.31 — write the first 4 server shortcuts to QuadTile slots
     *  + request a tile refresh so changes show without manual binding. */
    private void autoBindSlots(JSONArray items) {
        if (items == null) return;
        android.content.SharedPreferences sp = getSharedPreferences(
            CustomSosCreateActivity.PREFS, MODE_PRIVATE);
        android.content.SharedPreferences.Editor ed = sp.edit();
        for (int slot = 1; slot <= 4; slot++) {
            int idx = slot - 1;
            if (idx < items.length()) {
                JSONObject b = items.optJSONObject(idx);
                if (b == null) continue;
                ed.putInt("csos_slot_" + slot + "_id", b.optInt("id"))
                  .putString("csos_slot_" + slot + "_label",
                             b.optString("label", "SOS"))
                  .putString("csos_slot_" + slot + "_emoji",
                             b.optString("emoji", "🆘"));
            } else {
                ed.remove("csos_slot_" + slot + "_id")
                  .remove("csos_slot_" + slot + "_label")
                  .remove("csos_slot_" + slot + "_emoji");
            }
        }
        ed.apply();
        try {
            androidx.wear.tiles.TileService.getUpdater(this).requestUpdate(
                ae.servia.wear.tiles.CustomSosQuadTileService.class);
        } catch (Throwable ignored) {}
    }

    /** v1.24.29 — clickable "+ Create new" card at the top of the list. */
    private void addCreateCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundColor(0xFF065F46);
        card.setPadding(12, 10, 12, 10);
        LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        clp.bottomMargin = 6;
        card.setLayoutParams(clp);
        card.setClickable(true);

        TextView ico = new TextView(this);
        ico.setText("➕"); ico.setTextSize(22);
        card.addView(ico);

        TextView nm = new TextView(this);
        nm.setText("Create new shortcut");
        nm.setTextColor(0xFFFFFFFF); nm.setTextSize(13);
        nm.setTypeface(nm.getTypeface(), Typeface.BOLD);
        card.addView(nm);

        TextView meta = new TextView(this);
        meta.setText("Voice or type · pick service · save");
        meta.setTextColor(0xCCFFFFFF); meta.setTextSize(10);
        card.addView(meta);

        card.setOnClickListener(v ->
            startActivity(new Intent(this, CustomSosCreateActivity.class)));
        root.addView(card);
    }

    private void addCard(JSONObject b) {
        final int btnId = b.optInt("id");
        final String label = b.optString("label", "SOS");
        final String emoji = b.optString("emoji", "🆘");
        final String color = b.optString("color", "#DC2626");
        final boolean pinReq = b.optInt("pin_required", 0) == 1;
        final int tapCount = b.optInt("tap_count", 0);

        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        try { card.setBackgroundColor((int) Long.parseLong("FF" + color.replace("#", ""), 16)); }
        catch (Exception e) { card.setBackgroundColor(0xFFDC2626); }
        card.setPadding(12, 10, 12, 10);
        LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        clp.bottomMargin = 6;
        card.setLayoutParams(clp);
        card.setClickable(true);

        TextView ico = new TextView(this);
        ico.setText(emoji);
        ico.setTextSize(22);
        card.addView(ico);

        TextView nm = new TextView(this);
        nm.setText(label);
        nm.setTextColor(0xFFFFFFFF);
        nm.setTextSize(13);
        nm.setTypeface(nm.getTypeface(), Typeface.BOLD);
        card.addView(nm);

        TextView meta = new TextView(this);
        StringBuilder mb = new StringBuilder();
        if (tapCount > 0) mb.append("🔥 ").append(tapCount).append("x · ");
        if (pinReq) mb.append("🔒 PIN ");
        mb.append(b.optString("service_id", "").replace("_", " "));
        meta.setText(mb.toString());
        meta.setTextColor(0xCCFFFFFF);
        meta.setTextSize(10);
        card.addView(meta);

        card.setOnClickListener(v -> {
            if (pinReq) askPinThenDispatch(btnId, label);
            else dispatch(btnId, "");
        });
        root.addView(card);
    }

    private void askPinThenDispatch(int btnId, String label) {
        // Inline mini-modal with EditText
        ScrollView sv = new ScrollView(this);
        LinearLayout pl = new LinearLayout(this);
        pl.setOrientation(LinearLayout.VERTICAL);
        pl.setBackgroundColor(0xFF0F172A);
        pl.setPadding(14, 18, 14, 14);
        sv.addView(pl);
        setContentView(sv);

        TextView t = new TextView(this);
        t.setText("🔒 PIN required for\n" + label);
        t.setTextColor(0xFFFCD34D); t.setTextSize(13);
        t.setGravity(Gravity.CENTER);
        t.setTypeface(t.getTypeface(), Typeface.BOLD);
        t.setPadding(0, 0, 0, 12);
        pl.addView(t);

        EditText pinIn = new EditText(this);
        pinIn.setHint("PIN");
        pinIn.setHintTextColor(0xFF64748B);
        pinIn.setTextColor(0xFFFFFFFF);
        pinIn.setBackgroundColor(0xFF1E293B);
        pinIn.setPadding(10, 10, 10, 10);
        pinIn.setSingleLine();
        pinIn.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        pinIn.setGravity(Gravity.CENTER);
        pinIn.setTextSize(16);
        pl.addView(pinIn);

        TextView ok = button("✓ Verify & dispatch", 0xFFDC2626, 0xFFFFFFFF);
        ok.setOnClickListener(v -> {
            String p = pinIn.getText().toString().trim();
            if (p.isEmpty()) { Toast.makeText(this, "Enter PIN", Toast.LENGTH_SHORT).show(); return; }
            // Reset content view, then dispatch
            ScrollView wait = new ScrollView(this);
            LinearLayout wlp = new LinearLayout(this);
            wlp.setOrientation(LinearLayout.VERTICAL);
            wlp.setBackgroundColor(0xFF0F172A);
            wlp.setPadding(14, 22, 14, 14);
            wlp.setGravity(Gravity.CENTER);
            wait.addView(wlp);
            setContentView(wait);
            ProgressBar pb = new ProgressBar(this);
            wlp.addView(pb);
            TextView st = new TextView(this);
            st.setText("Dispatching…");
            st.setTextColor(0xFFFFFFFF); st.setTextSize(12);
            st.setGravity(Gravity.CENTER); st.setPadding(0, 12, 0, 0);
            wlp.addView(st);
            statusView = st; spinner = pb; root = wlp;
            dispatch(btnId, p);
        });
        pl.addView(ok);

        TextView cancel = button("Cancel", 0xFF334155, 0xFFCBD5E1);
        cancel.setOnClickListener(v -> { setContentView(sv); });
        cancel.setTextSize(11);
        pl.addView(cancel);
    }

    private void dispatch(int btnId, String pin) {
        bg.submit(() -> {
            try {
                JSONObject body = new JSONObject();
                if (pin != null && !pin.isEmpty()) body.put("pin", pin);
                URL u = new URL("https://servia.ae/api/sos/custom/" + btnId + "/dispatch");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Authorization", "Bearer " + WearAuth.getToken(this));
                con.setConnectTimeout(8000);
                con.setReadTimeout(15000);
                con.setRequestProperty("User-Agent", "ServiaWear/1.24.41 (Android Wear OS)");
                con.setDoOutput(true);
                try (OutputStream os = con.getOutputStream()) {
                    os.write(body.toString().getBytes("UTF-8"));
                }
                int code = con.getResponseCode();
                BufferedReader r = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(), "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line; while ((line = r.readLine()) != null) sb.append(line);
                r.close();
                if (code >= 200 && code < 300) {
                    JSONObject j = new JSONObject(sb.toString());
                    ui.post(() -> renderResult(j));
                } else {
                    final String err = sb.toString();
                    ui.post(() -> {
                        Toast.makeText(this, "⚠ " + err, Toast.LENGTH_LONG).show();
                        if (statusView != null) statusView.setText("⚠ " + err);
                    });
                }
            } catch (Exception e) {
                final String em = e.getMessage();
                ui.post(() -> Toast.makeText(this, "Network: " + em, Toast.LENGTH_LONG).show());
            }
        });
    }

    private void renderResult(JSONObject j) {
        if (root != null) {
            ScrollView sv = new ScrollView(this);
            LinearLayout pl = new LinearLayout(this);
            pl.setOrientation(LinearLayout.VERTICAL);
            pl.setBackgroundColor(0xFFDC2626);
            pl.setPadding(14, 22, 14, 14);
            sv.addView(pl);
            setContentView(sv);
            TextView st = new TextView(this);
            st.setText("✅ DISPATCHED " + j.optString("booking_id"));
            st.setTextColor(0xFFFCD34D); st.setTextSize(11);
            st.setTypeface(st.getTypeface(), Typeface.BOLD);
            st.setGravity(Gravity.CENTER);
            pl.addView(st);
            JSONObject vendor = j.optJSONObject("vendor");
            if (vendor != null) {
                TextView vn = new TextView(this);
                vn.setText(vendor.optString("name"));
                vn.setTextColor(0xFFFFFFFF); vn.setTextSize(15);
                vn.setTypeface(vn.getTypeface(), Typeface.BOLD);
                vn.setGravity(Gravity.CENTER); vn.setPadding(0, 8, 0, 4);
                pl.addView(vn);
                TextView vm = new TextView(this);
                vm.setText("⏱ " + j.optInt("eta_min") + " min · " + j.optDouble("distance_km") + " km · AED " + (int) j.optDouble("price_aed", 250));
                vm.setTextColor(0xFFFCD34D); vm.setTextSize(13);
                vm.setGravity(Gravity.CENTER); vm.setPadding(0, 0, 0, 8);
                pl.addView(vm);
                String phone = vendor.optString("phone");
                TextView call = button("📞 CALL " + phone, 0xFFFCD34D, 0xFF1E293B);
                call.setOnClickListener(v -> {
                    try {
                        Intent i = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + phone.replace(" ", "")));
                        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(i);
                    } catch (Exception ignored) {}
                });
                pl.addView(call);
            }
        }
    }

    private TextView button(String text, int bg, int fg) {
        TextView b = new TextView(this);
        b.setText(text); b.setTextColor(fg); b.setTextSize(13);
        b.setBackgroundColor(bg); b.setGravity(Gravity.CENTER);
        b.setPadding(8, 12, 8, 12);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 4;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }
}
