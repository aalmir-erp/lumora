package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * v1.24.29 — slot tile -> dispatch glue activity.
 *
 * One of the 5 CustomSosSlot{n}TileService tiles is tapped, which
 * launches us with intent extra "slot" = 1..5. We read the bound
 * button id from SharedPreferences ("servia_csos_slots") and POST
 * /api/sos/custom/{id}/dispatch, then render the vendor card.
 *
 * Same response handling as {@link MySosActivity#dispatch}.
 */
public class CustomSosSlotDispatchActivity extends Activity {

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
            onb.putExtra("next_class", CustomSosSlotDispatchActivity.class.getName());
            startActivity(onb); finish(); return;
        }

        int slot = getIntent().getIntExtra("slot", 0);
        if (slot < 1 || slot > 5) {
            Toast.makeText(this, "Slot not configured", Toast.LENGTH_SHORT).show();
            finish(); return;
        }

        SharedPreferences sp = getSharedPreferences(
            CustomSosCreateActivity.PREFS, MODE_PRIVATE);
        int btnId = sp.getInt("csos_slot_" + slot + "_id", 0);
        String label = sp.getString("csos_slot_" + slot + "_label", null);
        if (btnId == 0 || label == null) {
            Toast.makeText(this, "Slot " + slot + " is empty",
                           Toast.LENGTH_SHORT).show();
            startActivity(new Intent(this, CustomSosCreateActivity.class));
            finish(); return;
        }

        ScrollView sv = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(14, 22, 14, 14);
        root.setGravity(Gravity.CENTER);
        sv.addView(root);
        setContentView(sv);

        TextView t = new TextView(this);
        t.setText("⚡ SLOT " + slot + "\n" + label);
        t.setTextColor(0xFFFCD34D); t.setTextSize(13);
        t.setTypeface(t.getTypeface(), Typeface.BOLD);
        t.setGravity(Gravity.CENTER);
        t.setPadding(0, 0, 0, 12);
        root.addView(t);

        spinner = new ProgressBar(this);
        LinearLayout.LayoutParams sp2 = new LinearLayout.LayoutParams(40, 40);
        sp2.gravity = Gravity.CENTER_HORIZONTAL;
        spinner.setLayoutParams(sp2);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setText("Dispatching…");
        statusView.setTextColor(0xFFCBD5E1); statusView.setTextSize(11);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 8, 0, 0);
        root.addView(statusView);

        dispatch(btnId);
    }

    private void dispatch(int btnId) {
        bg.submit(() -> {
            try {
                JSONObject body = new JSONObject();
                URL u = new URL("https://servia.ae/api/sos/custom/"
                                + btnId + "/dispatch");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Authorization",
                    "Bearer " + WearAuth.getToken(this));
                con.setConnectTimeout(8000);
                con.setReadTimeout(15000);
                con.setRequestProperty("User-Agent", "ServiaWear/1.24.41 (Android Wear OS)");
                con.setDoOutput(true);
                try (OutputStream os = con.getOutputStream()) {
                    os.write(body.toString().getBytes("UTF-8"));
                }
                int code = con.getResponseCode();
                BufferedReader r = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(),
                    "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line; while ((line = r.readLine()) != null) sb.append(line);
                r.close();
                if (code >= 200 && code < 300) {
                    JSONObject j = new JSONObject(sb.toString());
                    ui.post(() -> renderResult(j));
                } else {
                    final String err = sb.toString();
                    ui.post(() -> {
                        spinner.setVisibility(View.GONE);
                        statusView.setText("⚠ " + err);
                    });
                }
            } catch (Exception e) {
                final String em = e.getMessage();
                ui.post(() -> {
                    spinner.setVisibility(View.GONE);
                    statusView.setText("⚠ " + (em == null ? "Network error" : em));
                });
            }
        });
    }

    private void renderResult(JSONObject j) {
        spinner.setVisibility(View.GONE);
        root.setBackgroundColor(0xFFDC2626);
        statusView.setText("✅ DISPATCHED · " + j.optString("booking_id"));
        statusView.setTextColor(0xFFFCD34D);
        statusView.setTypeface(statusView.getTypeface(), Typeface.BOLD);

        JSONObject vendor = j.optJSONObject("vendor");
        if (vendor != null) {
            TextView vn = new TextView(this);
            vn.setText(vendor.optString("name"));
            vn.setTextColor(0xFFFFFFFF); vn.setTextSize(15);
            vn.setTypeface(vn.getTypeface(), Typeface.BOLD);
            vn.setGravity(Gravity.CENTER); vn.setPadding(0, 8, 0, 4);
            root.addView(vn);

            TextView vm = new TextView(this);
            vm.setText("⏱ " + j.optInt("eta_min") + " min · "
                + j.optDouble("distance_km") + " km · AED "
                + (int) j.optDouble("price_aed", 250));
            vm.setTextColor(0xFFFCD34D); vm.setTextSize(12);
            vm.setGravity(Gravity.CENTER); vm.setPadding(0, 0, 0, 8);
            root.addView(vm);

            final String phone = vendor.optString("phone");
            if (phone != null && !phone.isEmpty()) {
                TextView call = new TextView(this);
                call.setText("📞 CALL " + phone);
                call.setTextColor(0xFF1E293B);
                call.setBackgroundColor(0xFFFCD34D);
                call.setTextSize(13); call.setGravity(Gravity.CENTER);
                call.setPadding(8, 12, 8, 12);
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT);
                lp.topMargin = 6;
                call.setLayoutParams(lp);
                call.setClickable(true);
                call.setOnClickListener(v -> {
                    try {
                        Intent i = new Intent(Intent.ACTION_DIAL,
                            Uri.parse("tel:" + phone.replace(" ", "")));
                        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                        startActivity(i);
                    } catch (Exception ignored) {}
                });
                root.addView(call);
            }
        }
    }
}
