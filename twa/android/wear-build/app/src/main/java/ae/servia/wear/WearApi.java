package ae.servia.wear;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Tiny shared HTTP helper used by every wear screen that talks to Servia.
 * Stays inside stdlib (HttpsURLConnection) so the wear APK stays small.
 *
 * Conversation state — we keep ONE chat session_id alive for the whole
 * watch session so successive mic taps continue the same conversation
 * (the LLM can refer to "the deep clean we just discussed" etc).
 */
public class WearApi {
    public static final String BASE = "https://servia.ae";

    private static final ExecutorService BG = Executors.newSingleThreadExecutor();
    private static final Handler UI = new Handler(Looper.getMainLooper());

    /** Chat session_id, set by /api/chat on first reply. */
    public static String sessionId = null;

    public interface Callback {
        void onSuccess(JSONObject json);
        void onError(String msg);
    }

    /** POST /api/chat → callback runs on UI thread. Pass ctx so the Bearer
     *  token from WearAuth is attached automatically (links chat history
     *  + chat-driven bookings to the customer's account). */
    public static void chat(Context ctx, String message, String phone, Callback cb) {
        post(ctx, "/api/chat", buildChatBody(message, phone), cb);
    }

    private static JSONObject buildChatBody(String message, String phone) {
        JSONObject b = new JSONObject();
        try {
            b.put("message", message);
            if (sessionId != null) b.put("session_id", sessionId);
            b.put("language", "en");
            if (phone != null && !phone.isEmpty()) b.put("phone", phone);
        } catch (Exception ignored) {}
        return b;
    }

    /** Generic POST with JSON body. ctx is used to attach Bearer token. */
    public static void post(Context ctx, String path, JSONObject body, Callback cb) {
        final String token = ctx == null ? null : WearAuth.getToken(ctx);
        BG.submit(() -> {
            try {
                URL u = new URL(BASE + path);
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Accept", "application/json");
                con.setRequestProperty("User-Agent", "Servia-Wear/1.24.4");
                if (token != null && !token.isEmpty()) {
                    con.setRequestProperty("Authorization", "Bearer " + token);
                }
                con.setConnectTimeout(8000);
                con.setReadTimeout(30000);   // chat replies can take ~10s
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
                    final JSONObject j = new JSONObject(sb.toString());
                    // Persist chat session id from replies
                    if (path.equals("/api/chat") && j.has("session_id")) {
                        sessionId = j.optString("session_id", sessionId);
                    }
                    UI.post(() -> cb.onSuccess(j));
                } else {
                    final String err = sb.toString();
                    UI.post(() -> cb.onError("HTTP " + code + ": " + err));
                }
            } catch (Exception e) {
                final String m = e.getMessage();
                UI.post(() -> cb.onError(m == null ? "Network error" : m));
            }
        });
    }
}
