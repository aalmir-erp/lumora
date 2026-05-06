package ae.servia.wear;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Wear-side identity. Persists customer phone, email, name + auth token
 * across app restarts so we never re-prompt the user, and so every wear
 * booking is bound to a real customer (visible in /account.html).
 *
 * Calls /api/auth/customer/wear-init on first save to (a) create the
 * customer record on the server if missing and (b) fetch a 30-day Bearer
 * session token. Subsequent dispatch / chat calls send the token.
 */
public final class WearAuth {
    private static final String PREFS = "servia_wear_auth";
    private static final String K_PHONE = "phone";
    private static final String K_EMAIL = "email";
    private static final String K_NAME  = "name";
    private static final String K_TOKEN = "token";

    private WearAuth() {}

    private static SharedPreferences sp(Context c) {
        return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
    public static boolean hasIdentity(Context c) {
        String p = sp(c).getString(K_PHONE, "");
        return p != null && !p.isEmpty();
    }
    public static String getPhone(Context c) { return sp(c).getString(K_PHONE, ""); }
    public static String getEmail(Context c) { return sp(c).getString(K_EMAIL, ""); }
    public static String getName(Context c)  { return sp(c).getString(K_NAME,  ""); }
    public static String getToken(Context c) { return sp(c).getString(K_TOKEN, ""); }

    public static void clear(Context c) {
        sp(c).edit().clear().apply();
        WearApi.sessionId = null;
    }

    public interface InitCallback {
        void onSuccess();
        void onError(String msg);
    }

    /** Save phone + email, call /api/auth/customer/wear-init, store token. */
    public static void initOnServer(final Context ctx, final String phone,
                                     final String email, final String name,
                                     final InitCallback cb) {
        final ExecutorService bg = Executors.newSingleThreadExecutor();
        bg.submit(() -> {
            try {
                JSONObject body = new JSONObject();
                body.put("phone", phone);
                if (email != null && !email.isEmpty()) body.put("email", email);
                if (name  != null && !name.isEmpty())  body.put("name",  name);
                body.put("source", "wear");

                URL u = new URL("https://servia.ae/api/auth/customer/wear-init");
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Accept", "application/json");
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
                    String token = j.optString("token", "");
                    JSONObject user = j.optJSONObject("user");
                    String canonPhone = user != null ? user.optString("phone", phone) : phone;
                    String canonEmail = user != null ? user.optString("email", email != null ? email : "") : (email != null ? email : "");
                    String canonName  = user != null ? user.optString("name",  name  != null ? name  : "") : (name  != null ? name  : "");
                    sp(ctx).edit()
                        .putString(K_PHONE, canonPhone)
                        .putString(K_EMAIL, canonEmail)
                        .putString(K_NAME,  canonName)
                        .putString(K_TOKEN, token)
                        .apply();
                    cb.onSuccess();
                } else {
                    cb.onError("HTTP " + code + ": " + sb.toString());
                }
            } catch (Exception e) {
                cb.onError(e.getMessage() == null ? "Network error" : e.getMessage());
            }
        });
    }
}
