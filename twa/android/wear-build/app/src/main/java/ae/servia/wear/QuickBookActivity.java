package ae.servia.wear;

import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Quick-book screen. Each button is a one-line natural-language booking
 * that gets pushed straight into /api/chat — the LLM picks it up,
 * resolves the customer's saved address + tomorrow's earliest slot,
 * and creates a real booking via the create_booking tool. The reply
 * (with tool_calls confirming what happened) is then rendered exactly
 * like a free-form chat reply, including the green "✅ Booking created"
 * chip and the spoken confirmation.
 *
 * Net effect: tap a service → booking exists in /account.html within
 * about 8 seconds. No more dummy Toast.
 */
public class QuickBookActivity extends ChatActivity {

    /** {one-tap label, AED hint, full prompt sent to /api/chat} */
    private static final String[][] SERVICES = {
        {"✨ Deep clean",  "AED 350+",
         "Book a deep cleaning at my saved home address tomorrow at 10am, "
       + "2 bedrooms, please use my default payment."},
        {"❄️ AC clean (3)", "AED 75/unit",
         "Book AC cleaning for 3 split units at my home tomorrow morning, "
       + "use my saved address and default payment."},
        {"👤 Maid 4 hrs",  "AED 25/hr",
         "Book a maid service for 4 hours at my home tomorrow morning, "
       + "saved address, default payment."},
        {"🔧 Handyman",    "AED 100+",
         "Book a 1-hour handyman call-out at my home tomorrow afternoon, "
       + "saved address, default payment."},
        {"🚗 Car wash",    "AED 60",
         "Book a car wash at my home tomorrow morning, "
       + "saved address, default payment."},
        {"🛟 Recovery",    "Tap once",
         "I need vehicle recovery right now — dispatch the closest tow truck."},
    };

    @Override
    protected boolean autoOpenMic() { return false; }

    @Override
    protected String micPrompt() { return "Or speak your own booking…"; }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Inject the prefill grid above the chat scroll. Easiest way: build a new
        // section with the buttons + add it to the existing root via the bubbles
        // container as a header.
        TextView prefillHeader = new TextView(this);
        prefillHeader.setText("⚡ ONE-TAP BOOK");
        prefillHeader.setTextColor(0xFFFCD34D);
        prefillHeader.setTextSize(11);
        prefillHeader.setGravity(Gravity.CENTER);
        prefillHeader.setPadding(0, 4, 0, 6);
        bubbles.addView(prefillHeader, 0);

        for (int i = 0; i < SERVICES.length; i++) {
            final String[] svc = SERVICES[i];
            TextView b = new TextView(this);
            b.setText(svc[0] + "  ·  " + svc[1]);
            b.setTextColor(0xFFFFFFFF);
            b.setBackgroundColor(0xFF14B8A6);
            b.setTextSize(12);
            b.setGravity(Gravity.CENTER);
            b.setPadding(8, 10, 8, 10);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = 4;
            b.setLayoutParams(lp);
            b.setClickable(true);
            b.setOnClickListener(v -> sendUserMessage(svc[2]));
            bubbles.addView(b, i + 1);
        }

        TextView divider = new TextView(this);
        divider.setText("— or speak your own —");
        divider.setTextColor(0xFF94A3B8);
        divider.setTextSize(10);
        divider.setGravity(Gravity.CENTER);
        divider.setPadding(0, 8, 0, 4);
        bubbles.addView(divider, SERVICES.length + 1);
    }
}
