package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
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

import java.util.ArrayList;

/**
 * First-run wear onboarding (v1.24.4). Collects phone + email + name so
 * every subsequent dispatch / chat / booking is bound to a real Servia
 * customer account, which means:
 *   - The booking shows up in /account.html on the phone or web.
 *   - Vendors get the customer's actual name and phone for callbacks.
 *   - Admin sees a real customer in the dispatch dashboard.
 *
 * Each field has BOTH a typing input AND a "🎙 Speak" button — so a user
 * with no on-watch keyboard preference can dictate. Phone field uses the
 * digits keyboard. Email field uses standard.
 *
 * On Save: POST /api/auth/customer/wear-init -> stores Bearer token in
 * SharedPreferences via WearAuth. Then launches the next_class activity
 * (passed in extras) so the user resumes whatever flow they tried first.
 */
public class OnboardingActivity extends Activity {

    private static final int REQ_VOICE_PHONE = 7771;
    private static final int REQ_VOICE_EMAIL = 7772;
    private static final int REQ_VOICE_NAME  = 7773;

    private EditText phoneField, emailField, nameField;
    private TextView statusView;
    private ProgressBar spinner;
    private TextView saveBtn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(12, 18, 12, 12);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("👋 WELCOME TO SERVIA");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 4);
        root.addView(header);

        TextView intro = new TextView(this);
        intro.setText("Quick one-time setup so we can confirm your bookings.");
        intro.setTextColor(0xFFCBD5E1);
        intro.setTextSize(10);
        intro.setGravity(Gravity.CENTER);
        intro.setPadding(0, 0, 0, 8);
        root.addView(intro);

        // PHONE
        addLabel(root, "📞 Mobile (UAE)");
        phoneField = field(InputType.TYPE_CLASS_PHONE, "0501234567");
        root.addView(phoneField);
        addMicButton(root, "🎙 Speak number", REQ_VOICE_PHONE);

        // EMAIL (optional but encouraged)
        addLabel(root, "📧 Email (optional)");
        emailField = field(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS,
                           "you@example.com");
        root.addView(emailField);
        addMicButton(root, "🎙 Speak email", REQ_VOICE_EMAIL);

        // NAME (optional)
        addLabel(root, "👤 Name (optional)");
        nameField = field(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_WORDS,
                          "Your name");
        root.addView(nameField);
        addMicButton(root, "🎙 Speak name", REQ_VOICE_NAME);

        // SAVE
        saveBtn = button("✓ Save & continue", 0xFFFCD34D, 0xFF1E293B);
        saveBtn.setOnClickListener(v -> save());
        root.addView(saveBtn);

        spinner = new ProgressBar(this);
        spinner.setIndeterminate(true);
        spinner.setVisibility(View.GONE);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(36, 36);
        sp.gravity = Gravity.CENTER_HORIZONTAL;
        sp.topMargin = 8;
        spinner.setLayoutParams(sp);
        root.addView(spinner);

        statusView = new TextView(this);
        statusView.setTextColor(0xFFFEE2E2);
        statusView.setTextSize(10);
        statusView.setGravity(Gravity.CENTER);
        statusView.setPadding(0, 6, 0, 4);
        root.addView(statusView);

        TextView privacy = new TextView(this);
        privacy.setText("We never share your data. Phone is used to confirm your bookings only.");
        privacy.setTextColor(0xFF64748B);
        privacy.setTextSize(9);
        privacy.setGravity(Gravity.CENTER);
        privacy.setPadding(0, 12, 0, 0);
        root.addView(privacy);
    }

    private void addLabel(LinearLayout root, String text) {
        TextView lbl = new TextView(this);
        lbl.setText(text);
        lbl.setTextColor(0xFFFCD34D);
        lbl.setTextSize(10);
        lbl.setPadding(0, 8, 0, 2);
        root.addView(lbl);
    }
    private EditText field(int inputType, String hint) {
        EditText f = new EditText(this);
        f.setInputType(inputType);
        f.setHint(hint);
        f.setHintTextColor(0xFF64748B);
        f.setTextColor(0xFFFFFFFF);
        f.setBackgroundColor(0xFF1E293B);
        f.setTextSize(13);
        f.setPadding(10, 10, 10, 10);
        f.setSingleLine();
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        f.setLayoutParams(lp);
        return f;
    }
    private void addMicButton(LinearLayout root, String label, int req) {
        TextView b = button(label, 0xFF334155, 0xFFFCD34D);
        b.setTextSize(11);
        b.setOnClickListener(v -> {
            try {
                Intent i = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
                i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                           RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
                i.putExtra(RecognizerIntent.EXTRA_PROMPT, label.replace("🎙 ", ""));
                startActivityForResult(i, req);
            } catch (Exception e) {
                Toast.makeText(this, "Voice not available", Toast.LENGTH_SHORT).show();
            }
        });
        root.addView(b);
    }
    private TextView button(String text, int bg, int fg) {
        TextView b = new TextView(this);
        b.setText(text);
        b.setTextColor(fg);
        b.setTextSize(13);
        b.setBackgroundColor(bg);
        b.setGravity(Gravity.CENTER);
        b.setPadding(10, 12, 10, 12);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = 4;
        b.setLayoutParams(lp);
        b.setClickable(true);
        return b;
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (res == RESULT_OK && data != null) {
            ArrayList<String> texts = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (texts == null || texts.isEmpty()) return;
            String t = texts.get(0);
            switch (req) {
                case REQ_VOICE_PHONE:
                    // Strip everything except digits + leading +
                    String digits = t.replaceAll("[^0-9+]", "");
                    phoneField.setText(digits);
                    break;
                case REQ_VOICE_EMAIL:
                    // Convert "at" → "@" and strip spaces
                    String email = t.toLowerCase()
                        .replace(" at ", "@")
                        .replace(" dot ", ".")
                        .replace(" ", "")
                        .trim();
                    emailField.setText(email);
                    break;
                case REQ_VOICE_NAME:
                    nameField.setText(t);
                    break;
            }
        }
    }

    private void save() {
        final String phone = phoneField.getText().toString().trim();
        final String email = emailField.getText().toString().trim();
        final String name  = nameField.getText().toString().trim();
        if (phone.isEmpty() || phone.length() < 7) {
            statusView.setText("⚠ Please enter a valid UAE mobile number.");
            return;
        }
        spinner.setVisibility(View.VISIBLE);
        saveBtn.setEnabled(false);
        statusView.setText("");
        WearAuth.initOnServer(this, phone, email, name, new WearAuth.InitCallback() {
            @Override public void onSuccess() {
                runOnUiThread(() -> {
                    spinner.setVisibility(View.GONE);
                    proceed();
                });
            }
            @Override public void onError(String msg) {
                runOnUiThread(() -> {
                    spinner.setVisibility(View.GONE);
                    saveBtn.setEnabled(true);
                    statusView.setText("⚠ " + msg);
                });
            }
        });
    }

    private void proceed() {
        try {
            String nextClass = getIntent().getStringExtra("next_class");
            if (nextClass != null && !nextClass.isEmpty()) {
                Intent next = new Intent();
                next.setClassName(getPackageName(), nextClass);
                // Forward all extras except next_class itself
                Bundle extras = getIntent().getExtras();
                if (extras != null) {
                    for (String k : extras.keySet()) {
                        if (!"next_class".equals(k)) {
                            Object v = extras.get(k);
                            if (v instanceof String)  next.putExtra(k, (String) v);
                            if (v instanceof Integer) next.putExtra(k, (Integer) v);
                            if (v instanceof Boolean) next.putExtra(k, (Boolean) v);
                        }
                    }
                }
                startActivity(next);
            } else {
                Toast.makeText(this, "✓ Welcome, " + WearAuth.getName(this), Toast.LENGTH_SHORT).show();
                startActivity(new Intent(this, MainActivity.class));
            }
        } catch (Exception ignored) {}
        finish();
    }
}
