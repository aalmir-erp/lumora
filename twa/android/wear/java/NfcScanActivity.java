package ae.servia.wear;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Typeface;
import android.net.Uri;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.os.Build;
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
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * v1.24.35 — Servia Wear NFC scan.
 *
 * Yes — modern Wear OS watches (Galaxy Watch 4+, Pixel Watch, Wear OS 3+)
 * have NFC hardware, and Android exposes NfcAdapter on Wear so a watch
 * activity can read the same tags the phone reads from /sos.html.
 *
 * Flow:
 *   1. User taps "📡 Scan NFC" on the watch (or assigns it to a slot
 *      on the watch face). This activity opens.
 *   2. enableForegroundDispatch() routes any tag scanned in the next
 *      30 seconds to onNewIntent().
 *   3. We read the first NDEF URL record. Expected URL shape:
 *         https://servia.ae/csos/{slug}
 *      where {slug} is the customer's pre-shared NFC tag id (already
 *      created via /api/sos/custom on phone or watch).
 *   4. We POST to /api/sos/custom/by-slug/{slug}/dispatch — same
 *      endpoint the phone /csos/<slug> page uses. Server returns the
 *      assigned vendor + booking id.
 *   5. Render vendor card with call button + show success notification.
 *
 * If the watch lacks NFC hardware (older models), we display a clear
 * "Your watch doesn't have NFC — use phone instead" message.
 */
public class NfcScanActivity extends Activity {

    private NfcAdapter nfc;
    private LinearLayout root;
    private TextView statusView;
    private ProgressBar spinner;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private static final Pattern SLUG_PATTERN =
        Pattern.compile("/csos/([A-Za-z0-9_-]+)");

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", NfcScanActivity.class.getName());
            startActivity(onb); finish(); return;
        }

        ScrollView sv = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(14, 22, 14, 14);
        sv.addView(root);
        setContentView(sv);

        TextView header = new TextView(this);
        header.setText("📡 NFC SCAN");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 8);
        root.addView(header);

        nfc = NfcAdapter.getDefaultAdapter(this);
        if (nfc == null) {
            TextView fail = new TextView(this);
            fail.setText("Your watch doesn't have NFC.\n\nUse the phone app to tap\nyour Servia tag.");
            fail.setTextColor(0xFFFCA5A5);
            fail.setTextSize(13);
            fail.setGravity(Gravity.CENTER);
            fail.setPadding(0, 12, 0, 12);
            root.addView(fail);
            return;
        }
        if (!nfc.isEnabled()) {
            TextView warn = new TextView(this);
            warn.setText("NFC is OFF.\nEnable it in Settings →\nConnections → NFC.");
            warn.setTextColor(0xFFFCD34D);
            warn.setTextSize(12);
            warn.setGravity(Gravity.CENTER);
            warn.setPadding(0, 12, 0, 12);
            root.addView(warn);
            return;
        }

        TextView prompt = new TextView(this);
        prompt.setText("Hold your wrist over\nyour Servia NFC tag.");
        prompt.setTextColor(0xFFFFFFFF);
        prompt.setTextSize(13);
        prompt.setGravity(Gravity.CENTER);
        prompt.setPadding(0, 8, 0, 12);
        root.addView(prompt);

        spinner = new ProgressBar(this);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(40, 40);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setText("Listening for tag…");
        statusView.setTextColor(0xFFCBD5E1);
        statusView.setTextSize(11);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 8, 0, 0);
        root.addView(statusView);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (nfc == null || !nfc.isEnabled()) return;
        Intent i = new Intent(this, getClass())
            .addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        int piFlags = PendingIntent.FLAG_UPDATE_CURRENT
            | (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M
                ? PendingIntent.FLAG_MUTABLE : 0);
        PendingIntent pi = PendingIntent.getActivity(this, 0, i, piFlags);
        IntentFilter[] filters = new IntentFilter[]{
            new IntentFilter(NfcAdapter.ACTION_NDEF_DISCOVERED),
            new IntentFilter(NfcAdapter.ACTION_TAG_DISCOVERED),
        };
        try {
            nfc.enableForegroundDispatch(this, pi, filters, null);
        } catch (Exception ignored) {}
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (nfc != null) {
            try { nfc.disableForegroundDispatch(this); }
            catch (Exception ignored) {}
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        String url = readNdefUrl(intent);
        if (url == null) {
            statusView.setText("⚠ Tag has no Servia URL.");
            return;
        }
        Matcher m = SLUG_PATTERN.matcher(url);
        if (!m.find()) {
            statusView.setText("⚠ Not a Servia tag.\n" + url);
            return;
        }
        String slug = m.group(1);
        statusView.setText("✓ Read tag: " + slug + "\nDispatching…");
        dispatch(slug);
    }

    /** Read first NDEF URI record from the tag. */
    private String readNdefUrl(Intent intent) {
        android.os.Parcelable[] msgs = intent.getParcelableArrayExtra(
            NfcAdapter.EXTRA_NDEF_MESSAGES);
        if (msgs == null) return null;
        for (android.os.Parcelable p : msgs) {
            if (!(p instanceof NdefMessage)) continue;
            for (NdefRecord r : ((NdefMessage) p).getRecords()) {
                Uri u = r.toUri();
                if (u != null) return u.toString();
                // Fallback: parse text record manually
                try {
                    if (r.getTnf() == NdefRecord.TNF_WELL_KNOWN
                            && java.util.Arrays.equals(r.getType(), NdefRecord.RTD_URI)) {
                        byte[] payload = r.getPayload();
                        if (payload.length > 1) {
                            return new String(payload, 1, payload.length - 1,
                                              StandardCharsets.UTF_8);
                        }
                    }
                } catch (Exception ignored) {}
            }
        }
        return null;
    }

    private void dispatch(String slug) {
        bg.submit(() -> {
            try {
                URL u = new URL("https://servia.ae/api/sos/custom/by-slug/"
                                + slug + "/dispatch");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Authorization",
                    "Bearer " + WearAuth.getToken(this));
                con.setConnectTimeout(8000);
                con.setReadTimeout(15000);
                con.setDoOutput(true);
                try (OutputStream os = con.getOutputStream()) {
                    os.write("{}".getBytes(StandardCharsets.UTF_8));
                }
                int code = con.getResponseCode();
                BufferedReader r = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(),
                    StandardCharsets.UTF_8));
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

        Toast.makeText(this, "✅ Dispatched · check the app",
                       Toast.LENGTH_LONG).show();

        JSONObject vendor = j.optJSONObject("vendor");
        if (vendor != null) {
            TextView vn = new TextView(this);
            vn.setText(vendor.optString("name"));
            vn.setTextColor(0xFFFFFFFF); vn.setTextSize(15);
            vn.setTypeface(vn.getTypeface(), Typeface.BOLD);
            vn.setGravity(Gravity.CENTER); vn.setPadding(0, 8, 0, 4);
            root.addView(vn);

            TextView vm = new TextView(this);
            vm.setText("⏱ " + j.optInt("eta_min") + " min · AED "
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
