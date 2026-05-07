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
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Servia one-tap vehicle-recovery activity.
 *
 * Lifecycle (designed so the user does NOTHING after the initial tap):
 *   1. Open  → request fine-location permission if missing.
 *   2. Read FusedLocationProviderClient with HIGH_ACCURACY (one-shot).
 *   3. POST {lat,lng,accuracy_m} to https://servia.ae/api/recovery/dispatch.
 *   4. Render vendor card: name · phone · ETA · distance · price.
 *   5. Single big button "📞 CALL NOW" → ACTION_DIAL the vendor number.
 *   6. Single small button "✓ Recovered" → POST .../complete.
 *
 * Total user actions to summon a tow truck: ONE TAP on the tile.
 */
public class RecoveryActivity extends Activity {

    private static final String API_BASE = "https://servia.ae";
    private static final int REQ_LOCATION = 4711;

    private LinearLayout root;
    private TextView statusView;
    private ProgressBar spinner;
    private FusedLocationProviderClient fused;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    private String vendorPhone;
    private long dispatchId = 0;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // v1.24.4 — onboarding gate so the booking is bound to a real
        // customer (visible in /account.html). For LITERAL emergencies this
        // adds ~10 sec friction the first time only — phone+email saved
        // forever after that.
        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", getClass().getName());
            startActivity(onb);
            finish();
            return;
        }

        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFFDC2626);  // RED
        root.setPadding(14, 22, 14, 14);
        root.setGravity(Gravity.CENTER_HORIZONTAL);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("🆘 SERVIA RECOVERY");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(12);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 6);
        root.addView(header);

        spinner = new ProgressBar(this);
        spinner.setIndeterminate(true);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(60, 60);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        sp.topMargin = 8;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setText("Locating…");
        statusView.setTextColor(0xFFFFFFFF);
        statusView.setTextSize(12);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 8, 0, 0);
        root.addView(statusView);

        fused = LocationServices.getFusedLocationProviderClient(this);

        if (hasLocationPermission()) {
            captureLocationAndDispatch();
        } else {
            requestPermissions(
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                             Manifest.permission.ACCESS_COARSE_LOCATION},
                REQ_LOCATION);
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
            if (hasLocationPermission()) {
                captureLocationAndDispatch();
            } else {
                fail("Location permission denied. Tap the SOS tile again to retry, or call +971 56 690 0255.");
            }
        }
    }

    private void captureLocationAndDispatch() {
        statusView.setText("📍 Getting your exact location…");
        try {
            CancellationTokenSource cts = new CancellationTokenSource();
            fused.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cts.getToken())
                .addOnSuccessListener(this::onLocation)
                .addOnFailureListener(e -> fallbackLastLocation());
        } catch (SecurityException se) {
            fail("Permission lost. Please retry.");
        }
    }

    private void fallbackLastLocation() {
        try {
            fused.getLastLocation()
                .addOnSuccessListener(loc -> {
                    if (loc != null) onLocation(loc);
                    else fail("Could not read GPS. Move outdoors and retry, or call +971 56 690 0255.");
                })
                .addOnFailureListener(e -> fail("GPS error: " + e.getMessage()));
        } catch (SecurityException se) {
            fail("Permission lost. Please retry.");
        }
    }

    private void onLocation(Location loc) {
        if (loc == null) { fail("No GPS fix yet. Try again in a moment."); return; }
        statusView.setText("🛟 Dispatching nearest recovery truck…");
        bg.submit(() -> postDispatch(loc));
    }

    private void postDispatch(Location loc) {
        try {
            JSONObject body = new JSONObject();
            body.put("lat", loc.getLatitude());
            body.put("lng", loc.getLongitude());
            body.put("accuracy_m", loc.getAccuracy());
            body.put("source", "watch");
            body.put("issue", "breakdown");
            body.put("service_id", "vehicle_recovery");
            // v1.24.4 — bind to the onboarded customer so the booking
            // shows up in /account.html bookings tab.
            body.put("customer_phone", WearAuth.getPhone(this));
            body.put("customer_email", WearAuth.getEmail(this));
            String n = WearAuth.getName(this);
            body.put("customer_name", (n == null || n.isEmpty()) ? Build.MODEL + " (Wear)" : n);

            URL u = new URL(API_BASE + "/api/recovery/dispatch");
            HttpURLConnection con = (HttpURLConnection) u.openConnection();
            con.setRequestMethod("POST");
            con.setRequestProperty("Content-Type", "application/json");
            con.setRequestProperty("Accept", "application/json");
            String tok = WearAuth.getToken(this);
            if (tok != null && !tok.isEmpty()) con.setRequestProperty("Authorization", "Bearer " + tok);
            con.setConnectTimeout(8000);
            con.setReadTimeout(12000);
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
            String line;
            while ((line = r.readLine()) != null) sb.append(line);
            r.close();
            if (code >= 200 && code < 300) {
                JSONObject j = new JSONObject(sb.toString());
                ui.post(() -> renderVendorCard(j));
            } else {
                final String err = sb.toString();
                ui.post(() -> fail("Dispatch failed (" + code + "). " + err));
            }
        } catch (Exception e) {
            ui.post(() -> fail("Network error: " + e.getMessage()));
        }
    }

    private void renderVendorCard(JSONObject j) {
        spinner.setVisibility(View.GONE);
        try {
            dispatchId = j.optLong("dispatch_id", 0);
            JSONObject vendor = j.getJSONObject("vendor");
            vendorPhone = vendor.optString("phone");
            String vendorName = vendor.optString("name");
            String company = vendor.optString("company", "");
            int eta = j.optInt("eta_min");
            double dist = j.optDouble("distance_km");
            double price = j.optDouble("price_aed", 250);
            String baseLabel = vendor.optString("base_label", "Servia base");
            double rating = vendor.optDouble("rating", 4.8);
            int jobs = vendor.optInt("completed_jobs", 0);
            String bookingId = j.optString("booking_id", "");

            statusView.setText("✅ TRUCK DISPATCHED");
            statusView.setTextColor(0xFFFCD34D);
            statusView.setTextSize(13);

            // Vendor name (big)
            TextView name = new TextView(this);
            name.setText(vendorName);
            name.setTextColor(0xFFFFFFFF);
            name.setTextSize(15);
            name.setTypeface(name.getTypeface(), android.graphics.Typeface.BOLD);
            name.setGravity(Gravity.CENTER);
            name.setPadding(0, 10, 0, 2);
            root.addView(name);

            TextView meta = new TextView(this);
            meta.setText("★ " + String.format("%.1f", rating) + "  ·  "
                       + jobs + " jobs  ·  " + baseLabel);
            meta.setTextColor(0xFFFEE2E2);
            meta.setTextSize(10);
            meta.setGravity(Gravity.CENTER);
            meta.setPadding(0, 0, 0, 8);
            root.addView(meta);

            // ETA + distance card
            LinearLayout etaCard = new LinearLayout(this);
            etaCard.setOrientation(LinearLayout.VERTICAL);
            etaCard.setBackgroundColor(0xFF0F172A);
            etaCard.setPadding(10, 8, 10, 8);
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
            cp.bottomMargin = 6;
            etaCard.setLayoutParams(cp);
            etaCard.setGravity(Gravity.CENTER_HORIZONTAL);

            TextView etaBig = new TextView(this);
            etaBig.setText("⏱ " + eta + " min");
            etaBig.setTextColor(0xFFFCD34D);
            etaBig.setTextSize(20);
            etaBig.setTypeface(etaBig.getTypeface(), android.graphics.Typeface.BOLD);
            etaBig.setGravity(Gravity.CENTER);
            etaCard.addView(etaBig);

            TextView etaSub = new TextView(this);
            etaSub.setText(String.format("%.1f km away · AED %.0f", dist, price));
            etaSub.setTextColor(0xFFCBD5E1);
            etaSub.setTextSize(11);
            etaSub.setGravity(Gravity.CENTER);
            etaCard.addView(etaSub);
            root.addView(etaCard);

            // Big yellow CALL button
            TextView callBtn = button("📞 CALL  " + vendorPhone, 0xFFFCD34D, 0xFF0F172A);
            callBtn.setTextSize(13);
            callBtn.setTypeface(callBtn.getTypeface(), android.graphics.Typeface.BOLD);
            callBtn.setOnClickListener(v -> dialVendor());
            root.addView(callBtn);

            // Booking + complete row
            TextView bidView = new TextView(this);
            bidView.setText("Booking #" + bookingId);
            bidView.setTextColor(0xFFFEE2E2);
            bidView.setTextSize(10);
            bidView.setGravity(Gravity.CENTER);
            bidView.setPadding(0, 8, 0, 4);
            root.addView(bidView);

            TextView completeBtn = button("✓ Recovered — close", 0xFF14B8A6, 0xFFFFFFFF);
            completeBtn.setOnClickListener(v -> markComplete());
            root.addView(completeBtn);

            TextView cancelBtn = button("✕ Cancel dispatch", 0xFF334155, 0xFFFEE2E2);
            cancelBtn.setOnClickListener(v -> markCancel());
            root.addView(cancelBtn);

        } catch (Exception e) {
            fail("Could not parse dispatch response: " + e.getMessage());
        }
    }

    private TextView button(String text, int bg, int fg) {
        TextView b = new TextView(this);
        b.setText(text);
        b.setTextColor(fg);
        b.setTextSize(12);
        b.setBackgroundColor(bg);
        b.setGravity(Gravity.CENTER);
        b.setPadding(8, 12, 8, 12);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = 4;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }

    private void dialVendor() {
        if (vendorPhone == null || vendorPhone.isEmpty()) return;
        try {
            Intent i = new Intent(Intent.ACTION_DIAL,
                Uri.parse("tel:" + vendorPhone.replace(" ", "")));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        } catch (Exception e) {
            Toast.makeText(this, "Call: " + vendorPhone, Toast.LENGTH_LONG).show();
        }
    }

    private void markComplete() {
        if (dispatchId == 0) { finish(); return; }
        bg.submit(() -> postSimple("/api/recovery/dispatch/" + dispatchId + "/complete",
            "{\"rating\":5}"));
        Toast.makeText(this, "✓ Marked recovered", Toast.LENGTH_SHORT).show();
        ui.postDelayed(this::finish, 700);
    }

    private void markCancel() {
        if (dispatchId == 0) { finish(); return; }
        bg.submit(() -> postSimple("/api/recovery/dispatch/" + dispatchId + "/cancel", "{}"));
        Toast.makeText(this, "Dispatch cancelled", Toast.LENGTH_SHORT).show();
        ui.postDelayed(this::finish, 500);
    }

    private void postSimple(String path, String body) {
        try {
            URL u = new URL(API_BASE + path);
            HttpURLConnection con = (HttpURLConnection) u.openConnection();
            con.setRequestMethod("POST");
            con.setRequestProperty("Content-Type", "application/json");
            con.setConnectTimeout(6000);
            con.setReadTimeout(8000);
                con.setRequestProperty("User-Agent", "ServiaWear/1.24.41 (Android Wear OS)");
            con.setDoOutput(true);
            try (OutputStream os = con.getOutputStream()) {
                os.write(body.getBytes("UTF-8"));
            }
            con.getResponseCode();   // fire-and-forget
            con.disconnect();
        } catch (Exception ignored) {}
    }

    private void fail(String msg) {
        spinner.setVisibility(View.GONE);
        statusView.setText("⚠ " + msg);
        statusView.setTextColor(0xFFFEE2E2);

        TextView callHotline = button("📞 CALL HOTLINE", 0xFFFCD34D, 0xFF0F172A);
        callHotline.setTypeface(callHotline.getTypeface(), android.graphics.Typeface.BOLD);
        callHotline.setOnClickListener(v -> {
            try {
                Intent i = new Intent(Intent.ACTION_DIAL, Uri.parse("tel:+971566900255"));
                i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(i);
            } catch (Exception ignored) {}
        });
        root.addView(callHotline);
    }
}
