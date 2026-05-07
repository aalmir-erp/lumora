package ae.servia.wear;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.location.Location;
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

import androidx.core.app.ActivityCompat;

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
 * v1.24.29 — view + refresh the customer's saved address from the watch.
 *
 *   - Pulls the saved address from /api/me (cached in SharedPreferences
 *     "servia_address") and shows: pin + area + emirate + last update.
 *   - "📍 Use current GPS" → captures FusedLocationProvider snapshot,
 *     POSTs {lat,lng} to /api/me/location, then refreshes display.
 *   - "Open phone editor" → fires an action that the phone app catches
 *     via WearMessageListenerService to open the full address editor on
 *     the phone (since on-watch typing of street/building is painful).
 *
 * The watch tile (LocationTileService) opens this activity directly.
 */
public class LocationActivity extends Activity {

    private static final int REQ_LOC = 7301;
    public static final String PREFS = "servia_address";

    private LinearLayout root;
    private TextView labelView;
    private TextView updatedView;
    private ProgressBar spinner;
    private TextView statusView;

    private FusedLocationProviderClient fused;
    private final ExecutorService bg = Executors.newSingleThreadExecutor();
    private final Handler ui = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", LocationActivity.class.getName());
            startActivity(onb); finish(); return;
        }

        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(14, 22, 14, 14);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("📍 MY ADDRESS");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 8);
        root.addView(header);

        labelView = new TextView(this);
        labelView.setTextColor(0xFFFFFFFF);
        labelView.setTextSize(14);
        labelView.setTypeface(labelView.getTypeface(), Typeface.BOLD);
        labelView.setGravity(Gravity.CENTER);
        root.addView(labelView);

        updatedView = new TextView(this);
        updatedView.setTextColor(0xFFCBD5E1);
        updatedView.setTextSize(11);
        updatedView.setGravity(Gravity.CENTER);
        updatedView.setPadding(0, 4, 0, 12);
        root.addView(updatedView);

        TextView gps = primaryBtn("📍 Use current GPS", 0xFF065F46);
        gps.setOnClickListener(v -> startGpsCapture());
        root.addView(gps);

        TextView phone = primaryBtn("📱 Edit on phone", 0xFF1E40AF);
        phone.setOnClickListener(v -> openPhoneEditor());
        root.addView(phone);

        spinner = new ProgressBar(this);
        spinner.setVisibility(View.GONE);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(36, 36);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setTextColor(0xFFCBD5E1); statusView.setTextSize(11);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 8, 0, 0);
        root.addView(statusView);

        fused = LocationServices.getFusedLocationProviderClient(this);

        renderCachedAddress();
        loadAddressFromServer();
    }

    private void renderCachedAddress() {
        SharedPreferences sp = getSharedPreferences(PREFS, MODE_PRIVATE);
        String area = sp.getString("area", null);
        String emirate = sp.getString("emirate", null);
        long ts = sp.getLong("ts", 0L);
        if (area != null) {
            labelView.setText(area + (emirate == null ? "" : ", " + emirate));
            updatedView.setText("Cached · " + agoText(ts));
        } else {
            labelView.setText("(no address yet)");
            updatedView.setText("Tap GPS to set");
        }
    }

    private String agoText(long ts) {
        if (ts <= 0) return "—";
        long sec = (System.currentTimeMillis() - ts) / 1000L;
        if (sec < 60) return sec + "s ago";
        if (sec < 3600) return (sec / 60) + "m ago";
        if (sec < 86400) return (sec / 3600) + "h ago";
        return (sec / 86400) + "d ago";
    }

    private void loadAddressFromServer() {
        bg.submit(() -> {
            try {
                URL u = new URL("https://servia.ae/api/me/location");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestProperty("Authorization",
                    "Bearer " + WearAuth.getToken(this));
                con.setConnectTimeout(8000);
                con.setReadTimeout(12000);
                int code = con.getResponseCode();
                BufferedReader r = new BufferedReader(new InputStreamReader(
                    code >= 200 && code < 300 ? con.getInputStream() : con.getErrorStream(),
                    "UTF-8"));
                StringBuilder sb = new StringBuilder();
                String line; while ((line = r.readLine()) != null) sb.append(line);
                r.close();
                if (code >= 200 && code < 300) {
                    JSONObject j = new JSONObject(sb.toString());
                    final String area = j.optString("area", null);
                    final String emirate = j.optString("emirate", null);
                    if (area != null) {
                        getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                            .putString("area", area)
                            .putString("emirate", emirate)
                            .putLong("ts", System.currentTimeMillis())
                            .apply();
                        ui.post(this::renderCachedAddress);
                    }
                }
            } catch (Exception ignored) { /* keep cached value */ }
        });
    }

    private void startGpsCapture() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                new String[]{Manifest.permission.ACCESS_FINE_LOCATION,
                             Manifest.permission.ACCESS_COARSE_LOCATION},
                REQ_LOC);
            return;
        }
        spinner.setVisibility(View.VISIBLE);
        statusView.setText("Capturing GPS…");
        try {
            CancellationTokenSource cts = new CancellationTokenSource();
            fused.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cts.getToken())
                 .addOnSuccessListener(this::pushLocation)
                 .addOnFailureListener(e -> {
                     spinner.setVisibility(View.GONE);
                     statusView.setText("⚠ GPS unavailable");
                 });
        } catch (SecurityException e) {
            spinner.setVisibility(View.GONE);
            statusView.setText("⚠ Permission denied");
        }
    }

    @Override
    public void onRequestPermissionsResult(int req, String[] perms, int[] grants) {
        super.onRequestPermissionsResult(req, perms, grants);
        if (req == REQ_LOC && grants.length > 0
                && grants[0] == PackageManager.PERMISSION_GRANTED) {
            startGpsCapture();
        } else {
            statusView.setText("⚠ Location permission denied");
        }
    }

    private void pushLocation(Location loc) {
        if (loc == null) {
            spinner.setVisibility(View.GONE);
            statusView.setText("⚠ No fix yet");
            return;
        }
        statusView.setText("Saving…");
        bg.submit(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("lat", loc.getLatitude());
                body.put("lng", loc.getLongitude());
                body.put("accuracy_m", loc.getAccuracy());
                URL u = new URL("https://servia.ae/api/me/location");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Authorization",
                    "Bearer " + WearAuth.getToken(this));
                con.setConnectTimeout(8000);
                con.setReadTimeout(15000);
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
                    final String area = j.optString("area",
                        loc.getLatitude() + ", " + loc.getLongitude());
                    final String emirate = j.optString("emirate", null);
                    getSharedPreferences(PREFS, MODE_PRIVATE).edit()
                        .putString("area", area)
                        .putString("emirate", emirate)
                        .putLong("ts", System.currentTimeMillis())
                        .apply();
                    ui.post(() -> {
                        spinner.setVisibility(View.GONE);
                        statusView.setText("✅ Saved");
                        renderCachedAddress();
                    });
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

    private void openPhoneEditor() {
        Toast.makeText(this,
            "Open Servia on your phone\n→ My account → Address",
            Toast.LENGTH_LONG).show();
    }

    private TextView primaryBtn(String text, int bg) {
        TextView b = new TextView(this);
        b.setText(text); b.setTextColor(0xFFFFFFFF); b.setTextSize(13);
        b.setBackgroundColor(bg); b.setGravity(Gravity.CENTER);
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
