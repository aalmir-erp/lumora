package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognizerIntent;
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

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * v1.24.29 — create a custom one-tap SOS button directly from the watch.
 * Until now the customer had to open the phone (servia.ae/sos.html) just
 * to add a shortcut. This activity lets them do it on the wrist:
 *   1. Speak (or type) a label, e.g. "Burj villa AC".
 *   2. Pick a service category (vehicle / ac / plumber / electrician /
 *      handyman / furniture / cleaning / pest).
 *   3. Pick payment (wallet | ask) and optional PIN.
 *   4. Save -> POST /api/sos/custom.
 *   5. Optionally bind to one of 5 home-screen tile slots so it can be
 *      pinned next to the watch-face for true one-tap dispatch.
 *
 * The tile slots are pre-registered in AndroidManifest as
 * CustomSosSlot{1..5}TileService and read SharedPreferences keys
 * "csos_slot_{n}_id" / "csos_slot_{n}_label" / "csos_slot_{n}_emoji"
 * to know which custom button to dispatch on tap. Wear OS doesn't allow
 * dynamic tile registration so we ship a fixed pool of 5 slots.
 */
public class CustomSosCreateActivity extends Activity {

    public static final String PREFS = "servia_csos_slots";

    private static final String[] SVC_IDS    = {
        "vehicle_recovery", "ac_repair", "plumber", "electrician",
        "handyman", "furniture_move", "deep_cleaning", "pest_control"
    };
    private static final String[] SVC_LABELS = {
        "🚗 Vehicle", "❄ AC", "🚿 Plumber", "⚡ Electric",
        "🔧 Handy", "🛋 Move", "🧹 Clean", "🐛 Pest"
    };

    private static final int REQ_VOICE = 6101;

    private LinearLayout root;
    private EditText labelIn;
    private EditText pinIn;
    private TextView statusView;
    private ProgressBar spinner;
    private int svcIdx = 0;
    private String paymentMethod = "ask";
    private boolean pinRequired = false;

    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", CustomSosCreateActivity.class.getName());
            startActivity(onb); finish(); return;
        }

        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(12, 18, 12, 14);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("➕ NEW SOS BUTTON");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 8);
        root.addView(header);

        // ---- Label (speak or type) ----
        TextView labelHint = small("Label (e.g. 'Burj villa AC')", 0xFFCBD5E1);
        root.addView(labelHint);

        labelIn = new EditText(this);
        labelIn.setHint("Burj villa AC");
        labelIn.setHintTextColor(0xFF64748B);
        labelIn.setTextColor(0xFFFFFFFF);
        labelIn.setBackgroundColor(0xFF1E293B);
        labelIn.setPadding(10, 10, 10, 10);
        labelIn.setSingleLine();
        labelIn.setTextSize(13);
        labelIn.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        root.addView(labelIn);

        TextView mic = primaryBtn("🎙 Speak label", 0xFF065F46);
        mic.setOnClickListener(v -> startVoice());
        root.addView(mic);

        // ---- Service category ----
        TextView svcHint = small("Service", 0xFFCBD5E1);
        svcHint.setPadding(0, 12, 0, 4);
        root.addView(svcHint);
        final TextView svcBtn = primaryBtn(SVC_LABELS[0], 0xFF1E40AF);
        svcBtn.setOnClickListener(v -> {
            svcIdx = (svcIdx + 1) % SVC_IDS.length;
            svcBtn.setText(SVC_LABELS[svcIdx] + "  (tap to cycle)");
        });
        root.addView(svcBtn);

        // ---- Payment ----
        TextView payHint = small("Payment", 0xFFCBD5E1);
        payHint.setPadding(0, 12, 0, 4);
        root.addView(payHint);
        final TextView payBtn = primaryBtn("💳 Ask each time", 0xFF334155);
        payBtn.setOnClickListener(v -> {
            if ("ask".equals(paymentMethod)) {
                paymentMethod = "wallet";
                payBtn.setText("👛 Wallet auto");
            } else {
                paymentMethod = "ask";
                payBtn.setText("💳 Ask each time");
            }
        });
        root.addView(payBtn);

        // ---- PIN (optional) ----
        TextView pinHint = small("PIN protect (optional)", 0xFFCBD5E1);
        pinHint.setPadding(0, 12, 0, 4);
        root.addView(pinHint);
        pinIn = new EditText(this);
        pinIn.setHint("4-digit PIN, leave blank for none");
        pinIn.setHintTextColor(0xFF64748B);
        pinIn.setTextColor(0xFFFFFFFF);
        pinIn.setBackgroundColor(0xFF1E293B);
        pinIn.setPadding(10, 10, 10, 10);
        pinIn.setSingleLine();
        pinIn.setTextSize(13);
        pinIn.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        root.addView(pinIn);

        // ---- Save ----
        TextView save = primaryBtn("✅ SAVE", 0xFFDC2626);
        save.setOnClickListener(v -> doSave());
        root.addView(save);

        statusView = new TextView(this);
        statusView.setTextColor(0xFFCBD5E1);
        statusView.setTextSize(11);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 8, 0, 0);
        root.addView(statusView);

        spinner = new ProgressBar(this);
        spinner.setVisibility(View.GONE);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(36, 36);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        spinner.setLayoutParams(sp);
        root.addView(spinner);
    }

    private void startVoice() {
        try {
            Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                       RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
            i.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak label");
            startActivityForResult(i, REQ_VOICE);
        } catch (Exception e) {
            Toast.makeText(this, "Voice not available, type instead.",
                           Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int req, int code, Intent data) {
        super.onActivityResult(req, code, data);
        if (req != REQ_VOICE || code != Activity.RESULT_OK || data == null) return;
        ArrayList<String> hits = data.getStringArrayListExtra(
            RecognizerIntent.EXTRA_RESULTS);
        if (hits != null && !hits.isEmpty()) {
            labelIn.setText(hits.get(0));
        }
    }

    private void doSave() {
        final String label = labelIn.getText() == null ? "" : labelIn.getText().toString().trim();
        if (label.isEmpty()) {
            Toast.makeText(this, "Label required", Toast.LENGTH_SHORT).show();
            return;
        }
        pinRequired = pinIn.getText() != null && pinIn.getText().toString().trim().length() >= 4;

        spinner.setVisibility(View.VISIBLE);
        statusView.setText("Saving…");

        bg.submit(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("label", label);
                body.put("service_id", SVC_IDS[svcIdx]);
                body.put("payment_method", paymentMethod);
                body.put("pin_required", pinRequired);
                if (pinRequired) {
                    body.put("pin", pinIn.getText().toString().trim());
                }
                URL u = new URL("https://servia.ae/api/sos/custom");
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
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(),
                    "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line; while ((line = r.readLine()) != null) sb.append(line);
                r.close();

                if (code >= 200 && code < 300) {
                    JSONObject j = new JSONObject(sb.toString());
                    JSONObject btn = j.optJSONObject("button");
                    final int btnId = btn == null ? 0 : btn.optInt("id");
                    final String emoji = btn == null ? "🆘" : btn.optString("emoji", "🆘");
                    ui.post(() -> showSlotPicker(btnId, label, emoji));
                } else {
                    final String err = sb.toString();
                    ui.post(() -> {
                        spinner.setVisibility(View.GONE);
                        statusView.setText("⚠ HTTP " + code + ": " + err);
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

    private void showSlotPicker(int btnId, String label, String emoji) {
        spinner.setVisibility(View.GONE);
        ScrollView sv = new ScrollView(this);
        LinearLayout pl = new LinearLayout(this);
        pl.setOrientation(LinearLayout.VERTICAL);
        pl.setBackgroundColor(0xFF065F46);
        pl.setPadding(14, 22, 14, 14);
        sv.addView(pl);
        setContentView(sv);

        TextView t = new TextView(this);
        t.setText("✅ SAVED\n" + label + "\n\nPin to a tile slot?");
        t.setTextColor(0xFFFFFFFF); t.setTextSize(12);
        t.setGravity(Gravity.CENTER);
        t.setTypeface(t.getTypeface(), Typeface.BOLD);
        t.setPadding(0, 0, 0, 12);
        pl.addView(t);

        SharedPreferences sp = getSharedPreferences(PREFS, MODE_PRIVATE);
        for (int i = 1; i <= 5; i++) {
            final int slot = i;
            String existing = sp.getString("csos_slot_" + slot + "_label", null);
            String slotLabel = existing == null
                ? ("Slot " + slot + "  (empty)")
                : ("Slot " + slot + "  · " + existing + " (replace)");
            TextView b = primaryBtn(slotLabel, existing == null ? 0xFF334155 : 0xFFB45309);
            b.setOnClickListener(v -> {
                sp.edit()
                  .putInt("csos_slot_" + slot + "_id", btnId)
                  .putString("csos_slot_" + slot + "_label", label)
                  .putString("csos_slot_" + slot + "_emoji", emoji)
                  .apply();
                Toast.makeText(this, "Pinned to slot " + slot
                    + ".\nLong-press watch face → Tiles → Servia · SOS Slot "
                    + slot, Toast.LENGTH_LONG).show();
                finish();
            });
            pl.addView(b);
        }

        TextView skip = primaryBtn("Skip — leave it in My SOS", 0xFF1E293B);
        skip.setOnClickListener(v -> finish());
        pl.addView(skip);
    }

    private TextView small(String text, int color) {
        TextView t = new TextView(this);
        t.setText(text); t.setTextColor(color); t.setTextSize(11);
        t.setPadding(2, 0, 0, 4);
        return t;
    }

    private TextView primaryBtn(String text, int bg) {
        TextView b = new TextView(this);
        b.setText(text); b.setTextColor(0xFFFFFFFF); b.setTextSize(13);
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
