package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Locale;

/**
 * Real-time Servia chat screen for the watch.
 *
 * Talks to /api/chat (the same LLM-backed endpoint used by the website).
 * The session_id is held in {@link WearApi#sessionId} so successive
 * questions stay in the same conversation thread, which means the LLM
 * can chain ("now book it for tomorrow morning") without forgetting
 * what "it" refers to.
 *
 * UX:
 *   [scroll history of bubbles]
 *   [🎙 tap & speak]      [⌨ open phone]
 *
 * Replies are BOTH shown as a yellow Servia bubble AND spoken aloud via
 * Android TextToSpeech so the user doesn't have to look at the watch.
 *
 * If the chat reply contained tool_calls (booking confirmed, quote
 * created etc.), we surface a small green confirmation chip.
 */
public class ChatActivity extends Activity implements TextToSpeech.OnInitListener {

    private static final int VOICE_REQ = 0xC4A7;

    protected ScrollView scroll;
    protected LinearLayout bubbles;
    protected ProgressBar spinner;
    protected TextView status;
    protected TextToSpeech tts;
    protected boolean ttsReady = false;

    /** Subclass override: open the mic immediately on launch. */
    protected boolean autoOpenMic() { return false; }

    /** Subclass override: prompt sent to mic prompt UI. */
    protected String micPrompt() { return "Ask Servia anything"; }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(10, 18, 10, 10);

        TextView header = new TextView(this);
        header.setText("🤖 SERVIA");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 4);
        root.addView(header);

        scroll = new ScrollView(this);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1.0f);
        scroll.setLayoutParams(sp);
        bubbles = new LinearLayout(this);
        bubbles.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(bubbles);
        root.addView(scroll);

        spinner = new ProgressBar(this);
        spinner.setIndeterminate(true);
        LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(36, 36);
        pp.gravity = Gravity.CENTER_HORIZONTAL;
        pp.topMargin = 4;
        spinner.setLayoutParams(pp);
        spinner.setVisibility(View.GONE);
        root.addView(spinner);

        status = new TextView(this);
        status.setTextColor(0xFFCBD5E1);
        status.setTextSize(10);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0, 2, 0, 4);
        root.addView(status);

        TextView mic = button("🎙 Tap & speak", 0xFFFCD34D, 0xFF7C2D12);
        mic.setOnClickListener(v -> startVoiceInput());
        root.addView(mic);

        setContentView(root);

        // Initialise TTS in the background — spoken replies kick in once ready.
        tts = new TextToSpeech(getApplicationContext(), this);

        addAssistantBubble("Hi! Ask me anything — book a clean, get a quote, "
            + "summon recovery, top up wallet. Tap the mic to speak.");

        if (autoOpenMic()) {
            scroll.postDelayed(this::startVoiceInput, 400);
        }
    }

    @Override
    public void onInit(int s) {
        ttsReady = (s == TextToSpeech.SUCCESS);
        if (ttsReady) {
            try {
                tts.setLanguage(Locale.US);
                tts.setSpeechRate(1.04f);
            } catch (Exception ignored) {}
        }
    }

    @Override
    protected void onDestroy() {
        try { if (tts != null) { tts.stop(); tts.shutdown(); } } catch (Exception ignored) {}
        super.onDestroy();
    }

    // ---------------------------------------------------------------- voice
    protected void startVoiceInput() {
        try {
            Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                       RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            i.putExtra(RecognizerIntent.EXTRA_PROMPT, micPrompt());
            i.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
            startActivityForResult(i, VOICE_REQ);
        } catch (Exception e) {
            Toast.makeText(this, "Voice not available on this watch", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == VOICE_REQ && res == RESULT_OK && data != null) {
            ArrayList<String> texts =
                data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (texts != null && !texts.isEmpty()) {
                sendUserMessage(texts.get(0));
            }
        }
    }

    // ---------------------------------------------------------------- chat round-trip
    public void sendUserMessage(String text) {
        if (text == null || text.trim().isEmpty()) return;
        addUserBubble(text);
        spinner.setVisibility(View.VISIBLE);
        status.setText("Servia is thinking…");
        WearApi.chat(text, new WearApi.Callback() {
            @Override public void onSuccess(JSONObject j) {
                spinner.setVisibility(View.GONE);
                String reply = j.optString("text", "");
                String mode  = j.optString("mode", "");
                JSONArray tcs = j.optJSONArray("tool_calls");
                String chip = summariseTools(tcs);
                if (reply.isEmpty()) reply = "(no reply)";
                addAssistantBubble(reply);
                if (chip != null) addConfirmChip(chip);
                status.setText(modeLabel(mode));
                speak(reply);
            }
            @Override public void onError(String msg) {
                spinner.setVisibility(View.GONE);
                status.setText("");
                addAssistantBubble("⚠ " + msg);
            }
        });
    }

    private String modeLabel(String mode) {
        if ("llm".equals(mode))         return "via Servia LLM";
        if ("fast".equals(mode))        return "via fast-path booking";
        if ("canned-job".equals(mode))  return "via canned reply";
        if ("agent_handling".equals(mode)) return "human team is replying";
        if (mode != null && !mode.isEmpty()) return "via " + mode;
        return "";
    }

    private String summariseTools(JSONArray tcs) {
        if (tcs == null || tcs.length() == 0) return null;
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < tcs.length(); i++) {
            JSONObject t = tcs.optJSONObject(i);
            if (t == null) continue;
            String name = t.optString("name", "");
            JSONObject in = t.optJSONObject("input");
            switch (name) {
                case "create_booking":
                    sb.append("✅ Booking created");
                    if (in != null) sb.append(" · ").append(in.optString("service_id", ""));
                    break;
                case "get_quote":
                    sb.append("💰 Quote computed");
                    if (in != null) sb.append(" · ").append(in.optString("service_id", ""));
                    break;
                case "list_slots":
                    sb.append("📅 Slots checked"); break;
                case "check_coverage":
                    sb.append("📍 Coverage checked"); break;
                case "create_invoice_for_booking":
                    sb.append("🧾 Invoice issued"); break;
                case "send_whatsapp":
                    sb.append("💬 WhatsApp sent"); break;
                default:
                    sb.append("• ").append(name);
            }
            if (i < tcs.length() - 1) sb.append("  ");
        }
        return sb.length() == 0 ? null : sb.toString();
    }

    protected void speak(String text) {
        if (!ttsReady || tts == null || text == null) return;
        try {
            // Strip emoji-heavy noise so TTS doesn't say "smiley face"
            String clean = text.replaceAll("[\\p{So}\\p{Cn}]", "").trim();
            if (clean.length() > 600) clean = clean.substring(0, 600);
            tts.speak(clean, TextToSpeech.QUEUE_FLUSH, null, "wear-tts");
        } catch (Exception ignored) {}
    }

    // ---------------------------------------------------------------- bubbles
    protected void addUserBubble(String text)      { addBubble(text, 0xFF334155, 0xFFFFFFFF, Gravity.RIGHT); }
    protected void addAssistantBubble(String text) { addBubble(text, 0xFFFCD34D, 0xFF1E293B, Gravity.LEFT);  }
    protected void addConfirmChip(String text) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(0xFFD1FAE5);
        tv.setBackgroundColor(0xFF065F46);
        tv.setTextSize(10);
        tv.setTypeface(tv.getTypeface(), Typeface.BOLD);
        tv.setPadding(8, 5, 8, 5);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.gravity = Gravity.CENTER_HORIZONTAL;
        lp.topMargin = 4;
        lp.bottomMargin = 6;
        tv.setLayoutParams(lp);
        bubbles.addView(tv);
        scrollDown();
    }

    private void addBubble(String text, int bg, int fg, int gravity) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(fg);
        tv.setBackgroundColor(bg);
        tv.setTextSize(12);
        tv.setPadding(10, 7, 10, 7);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.gravity = gravity;
        lp.topMargin = 4;
        lp.leftMargin = (gravity == Gravity.RIGHT) ? 30 : 0;
        lp.rightMargin = (gravity == Gravity.LEFT) ? 30 : 0;
        tv.setLayoutParams(lp);
        bubbles.addView(tv);
        scrollDown();
    }

    private void scrollDown() {
        scroll.postDelayed(() -> scroll.fullScroll(View.FOCUS_DOWN), 60);
    }

    private TextView button(String text, int bg, int fg) {
        TextView b = new TextView(this);
        b.setText(text);
        b.setTextColor(fg);
        b.setBackgroundColor(bg);
        b.setTextSize(12);
        b.setGravity(Gravity.CENTER);
        b.setPadding(10, 12, 10, 12);
        b.setTypeface(b.getTypeface(), Typeface.BOLD);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 6;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }
}
