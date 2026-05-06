package ae.servia.wear;

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

    /** POST /api/chat → callback runs on UI thread. */
    public static void chat(String message, Callback cb) {
        post("/api/chat", buildChatBody(message), cb);
    }

    private static JSONObject buildChatBody(String message) {
        JSONObject b = new JSONObject();
        try {
            b.put("message", message);
            if (sessionId != null) b.put("session_id", sessionId);
            b.put("language", "en");
        } catch (Exception ignored) {}
        return b;
    }

    /** Generic POST with JSON body. */
    public static void post(String path, JSONObject body, Callback cb) {
        BG.submit(() -> {
            try {
                URL u = new URL(BASE + path);
                HttpURLConnection con = (HttpURLConnection) u.openConnection();
                con.setRequestMethod("POST");
                con.setRequestProperty("Content-Type", "application/json");
                con.setRequestProperty("Accept", "application/json");
                con.setRequestProperty("User-Agent", "Servia-Wear/1.24.2");
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
