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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Multi-SOS launcher activity (v1.24.4). One activity, many tiles.
 *
 * Each SosXTileService passes a service_id via intent extra ("vehicle_recovery",
 * "furniture_move", "electrician", "plumber", "ac_cleaning", "handyman"). We:
 *   1. Gate behind the OnboardingActivity if the user hasn't given us
 *      phone+email yet — so every booking gets linked to a real customer.
 *   2. Capture the watch GPS via FusedLocationProviderClient.
 *   3. Show the user an optional NOTES voice/type field (e.g. "front-right
 *      tyre flat" / "kitchen light fittings cracked") + an optional
 *      "📷 Add photo from phone" deep link.
 *   4. POST to /api/recovery/dispatch with service_id, GPS, notes, customer
 *      auth token. Booking is created on the server with the customer's
 *      phone, so it shows up in /account.html bookings tab automatically.
 *   5. Render vendor card with one-tap CALL.
 */
public class SosLauncherActivity extends Activity {

    private static final int REQ_LOCATION = 4711;
    private static final int REQ_VOICE_NOTES = 4712;

    private LinearLayout root;
    private TextView statusView, categoryView, locView;
    private EditText notesField;
    private ProgressBar spinner;
    private FusedLocationProviderClient fused;
    private Location currentLoc;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private String serviceId = "vehicle_recovery";
    private String categoryLabel = "🆘 SERVIA SOS";
    private long dispatchId = 0;
    private String vendorPhone;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Intent in = getIntent();
        if (in != null) {
            serviceId    = strExtra(in, "service_id",    "vehicle_recovery");
            categoryLabel = strExtra(in, "category_label","🆘 SERVIA SOS");
        }

        // First-run gate: if no phone yet, open onboarding then come back.
        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", SosLauncherActivity.class.getName());
            onb.putExtra("service_id", serviceId);
            onb.putExtra("category_label", categoryLabel);
            startActivity(onb);
            finish();
            return;
        }

        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(colorForService(serviceId));
        root.setPadding(12, 18, 12, 12);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        scroll.addView(root);
        setContentView(scroll);

        categoryView = new TextView(this);
        categoryView.setText(categoryLabel);
        categoryView.setTextColor(0xFFFCD34D);
        categoryView.setTextSize(11);
        categoryView.setGravity(Gravity.CENTER);
        categoryView.setPadding(0, 0, 0, 4);
        root.addView(categoryView);

        spinner = new ProgressBar(this);
        spinner.setIndeterminate(true);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(48, 48);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        sp.topMargin = 6;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setText("📍 Locating you…");
        statusView.setTextColor(0xFFFFFFFF);
        statusView.setTextSize(12);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 6, 0, 4);
        root.addView(statusView);

        locView = new TextView(this);
        locView.setTextColor(0xFFE2E8F0);
        locView.setTextSize(10);
        locView.setGravity(Gravity.CENTER);
        locView.setVisibility(View.GONE);
        root.addView(locView);

        // Optional: notes
        TextView notesLbl = new TextView(this);
        notesLbl.setText("Add details (optional)");
        notesLbl.setTextColor(0xFFFCD34D);
        notesLbl.setTextSize(10);
        notesLbl.setGravity(Gravity.CENTER);
        notesLbl.setPadding(0, 12, 0, 2);
        root.addView(notesLbl);

        notesField = new EditText(this);
        notesField.setHint("e.g. flat front tyre · paint cracked");
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

        TextView callBtn = button("📞 Or call hotline", 0xFF334155, 0xFFFFFFFF);
        callBtn.setOnClickListener(v -> {
            try {
                Intent i = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:+971566900255"));
                i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(i);
            } catch (Exception ignored) {}
        });
        root.addView(callBtn);

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
            else statusView.setText("⚠ Location permission denied. Tap dispatch to use last-known location, or call hotline.");
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
        statusView.setText("✅ Location captured. Add details above (optional) and tap DISPATCH.");
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
            body.put("issue", "sos");
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
            callBtn.setOnClickListener(v -> {
                try {
                    Intent i = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + vendorPhone.replace(" ", "")));
                    i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(i);
                } catch (Exception ignored) {}
            });
            root.addView(callBtn);
        } catch (Exception e) {
            statusView.setText("⚠ Could not parse: " + e.getMessage());
        }
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
        lp.topMargin = 6;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }
}
