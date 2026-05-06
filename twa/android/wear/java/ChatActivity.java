package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;

/**
 * Chat screen — voice-input quick message. Uses the watch's built-in
 * speech recognition (RecognizerIntent.ACTION_RECOGNIZE_SPEECH) so we
 * don't need a custom mic UI. The transcribed text gets bundled and
 * (v1.25) sent to the paired phone for /api/chat dispatch.
 */
public class ChatActivity extends Activity {

    private static final int VOICE_REQ = 0xC4A7;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(20, 20, 20, 20);

        TextView t = new TextView(this);
        t.setText("🤖 ASK SERVIA\n\nTap below + speak your question.");
        t.setTextColor(0xFFE2E8F0);
        t.setTextSize(13);
        t.setGravity(Gravity.CENTER);
        root.addView(t);

        TextView btn = new TextView(this);
        btn.setText("🎙 Tap & speak");
        btn.setTextColor(0xFF7C2D12);
        btn.setBackgroundColor(0xFFFCD34D);
        btn.setTextSize(13);
        btn.setGravity(Gravity.CENTER);
        btn.setPadding(20, 14, 20, 14);
        btn.setClickable(true);
        btn.setOnClickListener(v -> startVoiceInput());
        root.addView(btn);

        setContentView(root);
    }

    private void startVoiceInput() {
        try {
            Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                       RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            i.putExtra(RecognizerIntent.EXTRA_PROMPT, "Ask Servia");
            startActivityForResult(i, VOICE_REQ);
        } catch (Exception e) {
            Toast.makeText(this, "Voice not available", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == VOICE_REQ && res == RESULT_OK && data != null) {
            ArrayList<String> texts =
                data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (texts != null && !texts.isEmpty()) {
                String q = texts.get(0);
                Toast.makeText(this, "Sent: " + q, Toast.LENGTH_LONG).show();
                // v1.25: forward q to phone-companion → /api/chat
            }
        }
    }
}
