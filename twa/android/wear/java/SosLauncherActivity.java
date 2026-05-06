package ae.servia.wear;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.net.Uri;
import android.os.Build;
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

import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;
import com.google.android.gms.location.Priority;
import com.google.android.gms.tasks.CancellationTokenSource;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Multi-SOS launcher (v1.24.6).
 *
 * Two-step UX matching the website's /sos.html flow:
 *   STEP 1 — pick the specific issue (e.g. for vehicle: battery /
 *            flat tyre / fuel out / locked out / tow / crash). The
 *            list of options depends on the service_id passed by the
 *            tile (Vehicle, Furniture, Electrician, Plumber, AC,
 *            Handyman).
 *   STEP 2 — capture GPS, optionally type/speak details, hit
 *            DISPATCH. Vendor card with one-tap CALL is shown after.
 *
 * If the user came in with no service_id (legacy SOS Recovery tile),
 * we default to vehicle_recovery + still show the issue picker so the
 * dispatch can be more specific to the vendor.
 */
public class SosLauncherActivity extends Activity {

    private static final int REQ_LOCATION = 4711;
    private static final int REQ_VOICE_NOTES = 4712;

    private LinearLayout root;
    private ScrollView scroll;
    private TextView statusView, locView;
    private EditText notesField;
    private ProgressBar spinner;
    private FusedLocationProviderClient fused;
    private Location currentLoc;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private String serviceId = "vehicle_recovery";
    private String categoryLabel = "🆘 SERVIA SOS";
    private String chosenIssue = null;          // set when user picks a sub-option in step 1
    private String chosenIssueLabel = null;
    private long dispatchId = 0;
    private String vendorPhone;

    // ---- Sub-options per service_id (mirrors web /sos.html SERVICES). ----
    private static final Map<String, String[][]> SUBS = new HashMap<>();
    static {
        SUBS.put("vehicle_recovery", new String[][]{
            {"breakdown",  "❓ Breakdown"},
            {"battery",    "🔋 Battery dead"},
            {"flat_tyre",  "🛞 Flat tyre"},
            {"fuel",       "⛽ Out of fuel"},
            {"locked_out", "🔑 Locked out"},
            {"crash",      "🚨 Crash / tow"}
        });
        SUBS.put("furniture_move", new String[][]{
            {"move_small",  "📦 Small move (1 van)"},
            {"move_big",    "🚚 Big move (truck)"},
            {"assemble",    "🔩 Assemble (IKEA)"},
            {"disassemble", "🪛 Disassemble"},
            {"repair",      "🛠 Repair / fix"},
            {"hang",        "🖼 Hang on wall"}
        });
        SUBS.put("electrician", new String[][]{
            {"no_power",    "⚡ No power"},
            {"breaker",     "⚙️ Tripping breaker"},
            {"install",     "💡 Install fixture"},
            {"socket",      "🔌 Socket / switch"},
            {"ceiling_fan", "🌀 Ceiling fan"},
            {"other",       "🛠 Other"}
        });
        SUBS.put("plumber", new String[][]{
            {"leak",     "💧 Leak"},
            {"clog",     "🚽 Clog"},
            {"no_water", "❌ No water"},
            {"heater",   "🔥 Water heater"},
            {"install",  "🔧 Install fixture"},
            {"other",    "🛠 Other"}
        });
        SUBS.put("ac_cleaning", new String[][]{
            {"not_cooling", "🥵 Not cooling"},
            {"gas_top",     "💨 Gas top-up"},
            {"service",     "🧹 Full service"},
            {"noise",       "🔊 Noisy unit"},
            {"leak",        "💧 Water leak"},
            {"new_install", "🆕 New install"}
        });
        SUBS.put("handyman", new String[][]{
            {"paint",     "🎨 Wall paint"},
            {"door_lock", "🚪 Door / lock"},
            {"curtain",   "🪟 Curtain rod"},
            {"tv_mount",  "📺 TV mount"},
            {"shelf",     "📚 Shelves"},
            {"other",     "🛠 Other"}
        });
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Intent in = getIntent();
        if (in != null) {
            serviceId    = strExtra(in, "service_id",    "vehicle_recovery");
            categoryLabel = strExtra(in, "category_label","🆘 SERVIA SOS");
        }

        // First-run gate.
        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", SosLauncherActivity.class.getName());
            onb.putExtra("service_id", serviceId);
            onb.putExtra("category_label", categoryLabel);
            startActivity(onb);
            finish();
            return;
        }

        scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(colorForService(serviceId));
        root.setPadding(12, 18, 12, 12);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        scroll.addView(root);
        setContentView(scroll);

        showStep1Subs();
    }

    // ---------- STEP 1: pick the specific issue ----------
    private void showStep1Subs() {
        root.removeAllViews();

        TextView header = new TextView(this);
        header.setText(categoryLabel);
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 4);
        root.addView(header);

        TextView prompt = new TextView(this);
        prompt.setText(promptFor(serviceId));
        prompt.setTextColor(0xFFFFFFFF);
        prompt.setTextSize(13);
        prompt.setGravity(Gravity.CENTER);
        prompt.setPadding(0, 0, 0, 8);
        root.addView(prompt);

        String[][] subs = SUBS.get(serviceId);
        if (subs == null) {
            // Unknown service id — go straight to step 2 with a generic issue
            chosenIssue = "general";
            chosenIssueLabel = "General";
            showStep2Dispatch();
            return;
        }
        for (final String[] s : subs) {
            TextView b = button(s[1], 0xFF1E293B, 0xFFFCD34D);
            b.setOnClickListener(v -> {
                chosenIssue = s[0];
                chosenIssueLabel = s[1];
                showStep2Dispatch();
            });
            root.addView(b);
        }

        TextView call = button("📞 Or call hotline", 0xFF334155, 0xFFFFFFFF);
        call.setTextSize(11);
        call.setOnClickListener(v -> dial("+971566900255"));
        root.addView(call);
    }

    private String promptFor(String svc) {
        switch (svc) {
            case "vehicle_recovery": return "What happened?";
            case "furniture_move":   return "What do you need?";
            case "electrician":      return "What's the issue?";
            case "plumber":          return "What's the issue?";
            case "ac_cleaning":      return "What's wrong with the AC?";
            case "handyman":         return "What needs fixing?";
            default:                 return "Pick the kind of help";
        }
    }

    // ---------- STEP 2: GPS + notes + dispatch ----------
    private void showStep2Dispatch() {
        root.removeAllViews();

        TextView header = new TextView(this);
        header.setText(categoryLabel + "  ›  " + chosenIssueLabel);
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(10);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 4);
        root.addView(header);

        spinner = new ProgressBar(this);
        spinner.setIndeterminate(true);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(48, 48);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        sp.topMargin = 6;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setText("📍 Getting your location…");
        statusView.setTextColor(0xFFFFFFFF);
        statusView.setTextSize(11);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 6, 0, 4);
        root.addView(statusView);

        locView = new TextView(this);
        locView.setTextColor(0xFFE2E8F0);
        locView.setTextSize(9);
        locView.setGravity(Gravity.CENTER);
        locView.setVisibility(View.GONE);
        root.addView(locView);

        TextView notesLbl = new TextView(this);
        notesLbl.setText("Add details (optional)");
        notesLbl.setTextColor(0xFFFCD34D);
        notesLbl.setTextSize(10);
        notesLbl.setGravity(Gravity.CENTER);
        notesLbl.setPadding(0, 12, 0, 2);
        root.addView(notesLbl);

        notesField = new EditText(this);
        notesField.setHint("e.g. front-right tyre, bring jack");
        notesField.setHintTextColor(0xFF94A3B8);
        notesField.setTextColor(0xFFFFFFFF);
        notesField.setBackgroundColor(0x55000000);
        notesField.setTextSize(11);
        notesField.setPadding(8, 8, 8, 8);
        notesField.setSingleLine(false);
        notesField.setMaxLines(3);
        notesField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        LinearLayout.LayoutParams nlp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        nlp.topMargin = 4;
        notesField.setLayoutParams(nlp);
        root.addView(notesField);

        TextView micNotes = button("🎙 Speak details", 0xFF334155, 0xFFFCD34D);
        micNotes.setTextSize(11);
        micNotes.setOnClickListener(v -> {
            try {
                Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                           RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                i.putExtra(RecognizerIntent.EXTRA_PROMPT, "Describe what's wrong");
                startActivityForResult(i, REQ_VOICE_NOTES);
            } catch (Exception e) {
                Toast.makeText(this, "Voice not available", Toast.LENGTH_SHORT).show();
            }
        });
        root.addView(micNotes);

        TextView dispatchBtn = button("🆘 DISPATCH NOW", 0xFFFCD34D, 0xFF7C2D12);
        dispatchBtn.setOnClickListener(v -> doDispatch());
        root.addView(dispatchBtn);

        TextView back = button("← Back to issues", 0xFF334155, 0xFFCBD5E1);
        back.setTextSize(11);
        back.setOnClickListener(v -> showStep1Subs());
        root.addView(back);

        TextView call = button("📞 Or call hotline", 0xFF334155, 0xFFFFFFFF);
        call.setTextSize(11);
        call.setOnClickListener(v -> dial("+971566900255"));
        root.addView(call);

        fused = LocationServices.getFusedLocationProviderClient(this);
        if (hasLocationPermission()) {
            captureLocation();
        } else {
            requestPermissions(
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                             Manifest.permission.ACCESS_COARSE_LOCATION},
                REQ_LOCATION);
        }
    }

    private static String strExtra(Intent i, String key, String def) {
        try { String v = i.getStringExtra(key); return v != null ? v : def; }
        catch (Exception e) { return def; }
    }

    private static int colorForService(String svc) {
        switch (svc) {
            case "vehicle_recovery": return 0xFFDC2626;
            case "furniture_move":   return 0xFF7C3AED;
            case "electrician":      return 0xFFFBBF24;
            case "plumber":          return 0xFF0EA5E9;
            case "ac_cleaning":      return 0xFF06B6D4;
            case "handyman":         return 0xFF16A34A;
            default:                 return 0xFFDC2626;
        }
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED
            || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(requestCode, permissions, grants);
        if (requestCode == REQ_LOCATION) {
            if (hasLocationPermission()) captureLocation();
            else statusView.setText("⚠ Location permission denied. Tap Dispatch anyway, or call hotline.");
        }
    }

    private void captureLocation() {
        try {
            CancellationTokenSource cts = new CancellationTokenSource();
            fused.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cts.getToken())
                .addOnSuccessListener(loc -> {
                    if (loc != null) onLocation(loc);
                    else fallbackLastLocation();
                })
                .addOnFailureListener(e -> fallbackLastLocation());
        } catch (SecurityException se) {
            statusView.setText("⚠ " + se.getMessage());
        }
    }
    private void fallbackLastLocation() {
        try {
            fused.getLastLocation()
                .addOnSuccessListener(loc -> {
                    if (loc != null) onLocation(loc);
                    else statusView.setText("⚠ Could not read GPS. Move outdoors and try again.");
                });
        } catch (SecurityException se) {}
    }

    private void onLocation(Location loc) {
        currentLoc = loc;
        spinner.setVisibility(View.GONE);
        statusView.setText("✅ Location captured. Tap DISPATCH.");
        locView.setText(String.format("%.5f, %.5f  (±%dm)",
            loc.getLatitude(), loc.getLongitude(), Math.round(loc.getAccuracy())));
        locView.setVisibility(View.VISIBLE);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == REQ_VOICE_NOTES && res == RESULT_OK && data != null) {
            ArrayList<String> texts = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (texts != null && !texts.isEmpty()) {
                String old = notesField.getText().toString();
                notesField.setText((old.isEmpty() ? "" : old + " ") + texts.get(0));
            }
        }
    }

    private void doDispatch() {
        if (currentLoc == null) {
            Toast.makeText(this, "Locating you, please wait…", Toast.LENGTH_SHORT).show();
            return;
        }
        spinner.setVisibility(View.VISIBLE);
        statusView.setText("🛟 Dispatching nearest " + categoryLabel + "…");
        final String notes = notesField.getText().toString().trim();
        bg.submit(() -> postDispatch(currentLoc, notes));
    }

    private void postDispatch(Location loc, String notes) {
        try {
            JSONObject body = new JSONObject();
            body.put("lat", loc.getLatitude());
            body.put("lng", loc.getLongitude());
            body.put("accuracy_m", loc.getAccuracy());
            body.put("source", "watch");
            body.put("issue", chosenIssue == null ? "sos" : chosenIssue);
            body.put("service_id", serviceId);
            body.put("notes", notes == null ? "" : notes);
            body.put("customer_phone", WearAuth.getPhone(this));
            body.put("customer_email", WearAuth.getEmail(this));
            body.put("customer_name",  WearAuth.getName(this));

            URL u = new URL("https://servia.ae/api/recovery/dispatch");
            HttpURLConnection con = (HttpURLConnection) u.openConnection();
            con.setRequestMethod("POST");
            con.setRequestProperty("Content-Type", "application/json");
            con.setRequestProperty("Accept", "application/json");
            String tok = WearAuth.getToken(this);
            if (tok != null && !tok.isEmpty()) con.setRequestProperty("Authorization", "Bearer " + tok);
            con.setConnectTimeout(8000);
            con.setReadTimeout(15000);
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
                ui.post(() -> renderVendor(j));
            } else {
                final String err = sb.toString();
                ui.post(() -> {
                    spinner.setVisibility(View.GONE);
                    statusView.setText("⚠ Dispatch failed (" + code + "). " + err);
                });
            }
        } catch (Exception e) {
            ui.post(() -> {
                spinner.setVisibility(View.GONE);
                statusView.setText("⚠ Network error: " + e.getMessage());
            });
        }
    }

    private void renderVendor(JSONObject j) {
        spinner.setVisibility(View.GONE);
        try {
            dispatchId = j.optLong("dispatch_id", 0);
            JSONObject vendor = j.getJSONObject("vendor");
            vendorPhone = vendor.optString("phone");
            int eta = j.optInt("eta_min");
            double dist = j.optDouble("distance_km");
            statusView.setText("✅ DISPATCHED — " + j.optString("booking_id"));

            TextView vname = new TextView(this);
            vname.setText(vendor.optString("name"));
            vname.setTextColor(0xFFFFFFFF);
            vname.setTextSize(15);
            vname.setGravity(Gravity.CENTER);
            vname.setPadding(0, 8, 0, 2);
            root.addView(vname);

            TextView vmeta = new TextView(this);
            vmeta.setText("⏱ " + eta + " min · " + String.format("%.1f", dist) + " km · AED "
                          + Math.round(j.optDouble("price_aed", 250)));
            vmeta.setTextColor(0xFFFCD34D);
            vmeta.setTextSize(13);
            vmeta.setGravity(Gravity.CENTER);
            vmeta.setPadding(0, 0, 0, 8);
            root.addView(vmeta);

            TextView callBtn = button("📞 CALL  " + vendorPhone, 0xFFFCD34D, 0xFF1E293B);
            callBtn.setOnClickListener(v -> dial(vendorPhone));
            root.addView(callBtn);
        } catch (Exception e) {
            statusView.setText("⚠ Could not parse: " + e.getMessage());
        }
    }

    private void dial(String number) {
        try {
            Intent i = new Intent(Intent.ACTION_DIAL,
                Uri.parse("tel:" + number.replace(" ", "")));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        } catch (Exception ignored) {}
    }

    private TextView button(String text, int bg, int fg) {
        TextView b = new TextView(this);
        b.setText(text);
        b.setTextColor(fg);
        b.setTextSize(13);
        b.setBackgroundColor(bg);
        b.setGravity(Gravity.CENTER);
        b.setPadding(8, 12, 8, 12);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 4;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }
}
