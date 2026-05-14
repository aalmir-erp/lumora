package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.text.InputType;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.EditText;
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
    protected TextView stopBtn;     // v1.24.3: visible Stop button while TTS speaks
    protected TextToSpeech tts;
    protected boolean ttsReady = false;
    protected boolean ttsSpeaking = false;
    protected EditText _hiddenTypeField;     // v1.24.15: legacy IME-action handle

    /** Subclass override: open the mic immediately on launch. */
    protected boolean autoOpenMic() { return false; }

    /** Subclass override: prompt sent to mic prompt UI. */
    protected String micPrompt() { return "Ask Servia anything"; }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // v1.24.4 — onboarding gate. If we don't yet have a phone we won't be
        // able to attribute a chat-driven booking back to the customer's
        // /account.html, so first-run users go through OnboardingActivity.
        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", getClass().getName());
            startActivity(onb);
            finish();
            return;
        }

        // v1.24.15 — Wear OS UX redesign. Earlier layout had 4 buttons
        // stacked which crowded the small round screen. New layout:
        //   ┌─────────────────────────┐
        //   │ 🤖 SERVIA          🗑   │  ← header + tiny clear-icon
        //   │                         │
        //   │  scrollable bubbles     │
        //   │  …                      │
        //   │                         │
        //   │  status (10sp)          │
        //   │  ┌─────────────────┐   │
        //   │  │ 🎙 SPEAK        │   │  ← big primary, full width
        //   │  └─────────────────┘   │
        //   │  ┌─────────────────┐   │
        //   │  │ ⌨ TYPE          │   │  ← secondary, full width
        //   │  └─────────────────┘   │
        //   │  ⏹ Stop voice (only when TTS speaking)
        //   └─────────────────────────┘
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(10, 16, 10, 10);

        // Header row: title + tiny clear button
        LinearLayout headerRow = new LinearLayout(this);
        headerRow.setOrientation(LinearLayout.HORIZONTAL);
        headerRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView header = new TextView(this);
        header.setText("🤖 SERVIA");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams hlp = new LinearLayout.LayoutParams(
            0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        header.setLayoutParams(hlp);
        headerRow.addView(header);
        TextView clearBtn = new TextView(this);
        clearBtn.setText("🗑");
        clearBtn.setTextColor(0xFF94A3B8);
        clearBtn.setTextSize(13);
        clearBtn.setPadding(8, 4, 4, 4);
        clearBtn.setClickable(true);
        clearBtn.setOnClickListener(v -> {
            WearChatHistory.clear();
            bubbles.removeAllViews();
            addAssistantBubble(welcomeText());
        });
        headerRow.addView(clearBtn);
        root.addView(headerRow);

        // Scroll area for bubbles — takes max available space
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
        LinearLayout.LayoutParams pp = new LinearLayout.LayoutParams(28, 28);
        pp.gravity = Gravity.CENTER_HORIZONTAL;
        pp.topMargin = 2;
        spinner.setLayoutParams(pp);
        spinner.setVisibility(View.GONE);
        root.addView(spinner);

        status = new TextView(this);
        status.setTextColor(0xFFCBD5E1);
        status.setTextSize(9);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0, 2, 0, 4);
        root.addView(status);

        TextView mic = button("🎙 SPEAK", 0xFFFCD34D, 0xFF7C2D12);
        mic.setTextSize(13);
        mic.setOnClickListener(v -> { stopSpeaking(); startVoiceInput(); });
        mic.setOnLongClickListener(v -> { stopSpeaking(); return true; });
        root.addView(mic);

        // v1.24.15 — TYPE button opens a dedicated fullscreen input sheet
        // (cleaner than cramming an EditText into the chat view).
        TextView typeBtn = button("⌨ TYPE", 0xFF14B8A6, 0xFFFFFFFF);
        typeBtn.setTextSize(12);
        typeBtn.setOnClickListener(v -> openTypeSheet());
        root.addView(typeBtn);

        // Hidden EditText kept for IME-action-send compatibility (legacy)
        EditText typeField = new EditText(this);
        typeField.setVisibility(View.GONE);
        typeField.setSingleLine();
        typeField.setInputType(InputType.TYPE_CLASS_TEXT
                              | InputType.TYPE_TEXT_VARIATION_LONG_MESSAGE);
        typeField.setImeOptions(EditorInfo.IME_ACTION_SEND);
        typeField.setOnEditorActionListener((v, actionId, event) -> {
            boolean send = (actionId == EditorInfo.IME_ACTION_SEND
                || actionId == EditorInfo.IME_ACTION_DONE
                || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER));
            if (send) {
                String txt = typeField.getText().toString().trim();
                if (!txt.isEmpty()) {
                    stopSpeaking();
                    sendUserMessage(txt);
                    typeField.setText("");
                }
                return true;
            }
            return false;
        });
        root.addView(typeField);
        _hiddenTypeField = typeField;

        // Visible "⏹ Stop" button shown while TTS is speaking; hidden otherwise.
        stopBtn = button("⏹ Stop voice", 0xFF334155, 0xFFFFFFFF);
        stopBtn.setTextSize(10);
        stopBtn.setOnClickListener(v -> stopSpeaking());
        stopBtn.setVisibility(View.GONE);
        root.addView(stopBtn);

        // (legacy var kept for compile-only; real new-chat lives in header now)
        TextView newChatBtn = button("", 0xFF334155, 0xFFCBD5E1);
        newChatBtn.setVisibility(View.GONE);
        newChatBtn.setTextSize(10);
        newChatBtn.setOnClickListener(v -> {
            WearChatHistory.clear();
            bubbles.removeAllViews();
            addAssistantBubble(welcomeText());
        });
        root.addView(newChatBtn);

        setContentView(root);

        // Initialise TTS in the background — spoken replies kick in once ready.
        tts = new TextToSpeech(getApplicationContext(), this);

        // v1.24.4 — restore prior conversation if any. Going back and coming
        // back no longer wipes the chat.
        if (WearChatHistory.isEmpty()) {
            addAssistantBubble(welcomeText());
        } else {
            for (WearChatHistory.Bubble b : WearChatHistory.snapshot()) {
                if (b.side == WearChatHistory.Side.USER)        addBubble(b.text, 0xFF334155, 0xFFFFFFFF, Gravity.RIGHT);
                else if (b.side == WearChatHistory.Side.SERVIA) addBubble(b.text, 0xFFFCD34D, 0xFF1E293B, Gravity.LEFT);
                else                                            renderChip(b.text);
            }
        }

        if (autoOpenMic()) {
            scroll.postDelayed(this::startVoiceInput, 400);
        }
    }

    private String welcomeText() {
        String name = WearAuth.getName(this);
        return (name != null && !name.isEmpty() ? "Hi " + name + "! " : "Hi! ")
             + "Ask me anything — book a service, get a quote, summon recovery, "
             + "top up wallet. Speak or type.";
    }

    @Override
    public void onInit(int s) {
        ttsReady = (s == TextToSpeech.SUCCESS);
        if (ttsReady) {
            try {
                tts.setLanguage(Locale.US);
                tts.setSpeechRate(1.04f);
                // Track when TTS starts/stops so the Stop button shows correctly
                tts.setOnUtteranceProgressListener(new android.speech.tts.UtteranceProgressListener() {
                    @Override public void onStart(String uid) {
                        ttsSpeaking = true;
                        runOnUiThread(() -> stopBtn.setVisibility(View.VISIBLE));
                    }
                    @Override public void onDone(String uid) {
                        ttsSpeaking = false;
                        runOnUiThread(() -> stopBtn.setVisibility(View.GONE));
                    }
                    @Override public void onError(String uid) {
                        ttsSpeaking = false;
                        runOnUiThread(() -> stopBtn.setVisibility(View.GONE));
                    }
                });
            } catch (Exception ignored) {}
        }
    }

    /** Cut TTS playback immediately. Called when user taps mic again, taps
     *  the Stop button, or long-presses mic. */
    protected void stopSpeaking() {
        try {
            if (tts != null) tts.stop();
        } catch (Exception ignored) {}
        ttsSpeaking = false;
        if (stopBtn != null) stopBtn.setVisibility(View.GONE);
    }

    @Override
    protected void onDestroy() {
        try { if (tts != null) { tts.stop(); tts.shutdown(); } } catch (Exception ignored) {}
        super.onDestroy();
    }

    // ---------------------------------------------------------------- voice
    protected void startVoiceInput() {
        // Always silence any current TTS before listening — the recogniser
        // would pick up Servia's own voice as input otherwise.
        stopSpeaking();
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

    /** Open a fullscreen type-input sheet (cleaner than embedding an
     *  EditText in the cramped chat view). v1.24.15. */
    protected void openTypeSheet() {
        final android.app.Dialog dlg = new android.app.Dialog(this,
            android.R.style.Theme_DeviceDefault_NoActionBar_Fullscreen);
        LinearLayout sheet = new LinearLayout(this);
        sheet.setOrientation(LinearLayout.VERTICAL);
        sheet.setBackgroundColor(0xFF0F172A);
        sheet.setPadding(14, 22, 14, 14);

        TextView t = new TextView(this);
        t.setText("⌨ TYPE MESSAGE");
        t.setTextColor(0xFFFCD34D);
        t.setTextSize(11);
        t.setTypeface(t.getTypeface(), Typeface.BOLD);
        t.setGravity(Gravity.CENTER);
        t.setPadding(0, 0, 0, 8);
        sheet.addView(t);

        final EditText input = new EditText(this);
        input.setHint("Type then tap send…");
        input.setHintTextColor(0xFF64748B);
        input.setTextColor(0xFFFFFFFF);
        input.setBackgroundColor(0xFF1E293B);
        input.setPadding(10, 10, 10, 10);
        input.setTextSize(13);
        input.setMinLines(2); input.setMaxLines(4);
        input.setInputType(InputType.TYPE_CLASS_TEXT
                          | InputType.TYPE_TEXT_FLAG_MULTI_LINE
                          | InputType.TYPE_TEXT_VARIATION_LONG_MESSAGE);
        sheet.addView(input);

        TextView send = button("✉ Send", 0xFF14B8A6, 0xFFFFFFFF);
        send.setOnClickListener(v -> {
            String txt = input.getText().toString().trim();
            if (!txt.isEmpty()) { stopSpeaking(); sendUserMessage(txt); }
            dlg.dismiss();
        });
        sheet.addView(send);

        TextView cancel = button("Cancel", 0xFF334155, 0xFFCBD5E1);
        cancel.setTextSize(11);
        cancel.setOnClickListener(v -> dlg.dismiss());
        sheet.addView(cancel);

        dlg.setContentView(sheet);
        dlg.show();
        // Auto-focus the input + show keyboard
        input.requestFocus();
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
        WearChatHistory.add(WearChatHistory.Side.USER, text);
        spinner.setVisibility(View.VISIBLE);
        status.setText("Servia is thinking…");
        String phone = WearAuth.getPhone(this);
        WearApi.chat(this, text, phone, new WearApi.Callback() {
            @Override public void onSuccess(JSONObject j) {
                spinner.setVisibility(View.GONE);
                String reply = j.optString("text", "");
                String mode  = j.optString("mode", "");
                JSONArray tcs = j.optJSONArray("tool_calls");
                String chip = summariseTools(tcs);
                if (reply.isEmpty()) reply = "(no reply)";
                addAssistantBubble(reply);
                WearChatHistory.add(WearChatHistory.Side.SERVIA, reply);
                if (chip != null) {
                    addConfirmChip(chip);
                    WearChatHistory.add(WearChatHistory.Side.CHIP, chip);
                }
                status.setText(modeLabel(mode));
                speak(reply);
            }
            @Override public void onError(String msg) {
                spinner.setVisibility(View.GONE);
                status.setText("");
                addAssistantBubble("⚠ " + msg);
                WearChatHistory.add(WearChatHistory.Side.SERVIA, "⚠ " + msg);
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
            // Pass utteranceId so OnUtteranceProgressListener fires; this
            // toggles the Stop button's visibility for v1.24.3.
            android.os.Bundle p = new android.os.Bundle();
            tts.speak(clean, TextToSpeech.QUEUE_FLUSH, p, "wear-tts");
        } catch (Exception ignored) {}
    }

    // ---------------------------------------------------------------- bubbles
    protected void addUserBubble(String text)      { addBubble(text, 0xFF334155, 0xFFFFFFFF, Gravity.RIGHT); }
    protected void addAssistantBubble(String text) { addBubble(text, 0xFFFCD34D, 0xFF1E293B, Gravity.LEFT);  }
    protected void addConfirmChip(String text) { renderChip(text); }

    protected void renderChip(String text) {
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
