package ae.servia.wear;

import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Quote screen. Each chip pushes a natural-language quote question into
 * /api/chat — the LLM uses the get_quote tool and sends back the full
 * AED breakdown, which we then render as a Servia bubble + speak aloud.
 *
 * Net effect: tap "Deep clean 2BR" → ~3 seconds → "Deep cleaning, 2 BR,
 * 2 cleaners, 4 hrs: AED 580 incl. VAT (was AED 680, first-time discount)."
 */
public class QuoteActivity extends ChatActivity {

    /** {chip label, prompt for /api/chat} */
    private static final String[][] QUERIES = {
        {"✨ Deep clean 2BR",   "How much for a deep clean of a 2-bedroom apartment in Dubai Marina?"},
        {"❄️ AC clean (3)",     "Quote me AC cleaning for 3 split units in JLT."},
        {"👤 Maid 4 hrs",       "How much is 4 hours of maid service in Downtown Dubai?"},
        {"🔧 Handyman 1 hr",    "Quote a 1-hour handyman call-out in Business Bay."},
        {"🚗 Car wash",         "How much for a car wash at home in Marina?"},
        {"🛟 Recovery",         "Quote me roadside vehicle recovery in Dubai."},
        {"🪟 Window clean",     "Quote window cleaning for a 2BR apartment, 6 windows."},
        {"🛟 Pool service",     "Quote weekly pool maintenance for a 6×3 m pool in Arabian Ranches."},
    };

    @Override
    protected boolean autoOpenMic() { return false; }

    @Override
    protected String micPrompt() { return "Or speak your own quote question…"; }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        TextView header = new TextView(this);
        header.setText("💰 QUICK QUOTE");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 4, 0, 6);
        bubbles.addView(header, 0);

        for (int i = 0; i < QUERIES.length; i++) {
            final String[] q = QUERIES[i];
            TextView b = new TextView(this);
            b.setText(q[0]);
            b.setTextColor(0xFFFFFFFF);
            b.setBackgroundColor(0xFF6366F1);
            b.setTextSize(12);
            b.setGravity(Gravity.CENTER);
            b.setPadding(8, 10, 8, 10);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = 4;
            b.setLayoutParams(lp);
            b.setClickable(true);
            b.setOnClickListener(v -> sendUserMessage(q[1]));
            bubbles.addView(b, i + 1);
        }

        TextView divider = new TextView(this);
        divider.setText("— or speak your own —");
        divider.setTextColor(0xFF94A3B8);
        divider.setTextSize(10);
        divider.setGravity(Gravity.CENTER);
        divider.setPadding(0, 8, 0, 4);
        bubbles.addView(divider, QUERIES.length + 1);
    }
}
