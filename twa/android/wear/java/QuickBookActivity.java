package ae.servia.wear;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Quick-book activity — 4 service buttons, native UI. Tap → sends a
 * /servia/quick-book/<service> message to the paired phone via the
 * Wearable Data Layer (phone-companion service in v1.25 receives it
 * and opens /book.html?service=<id> on the phone). Until then we just
 * Toast a confirmation.
 */
public class QuickBookActivity extends Activity {

    private static final String[][] SERVICES = {
        {"deep_cleaning", "✨ Deep Clean", "AED 350+"},
        {"ac_cleaning",   "❄️ AC Service", "AED 75/unit"},
        {"maid_service",  "👤 Maid",       "AED 25/hr"},
        {"handyman",      "🔧 Handyman",   "AED 100+"},
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F766E);
        root.setPadding(12, 18, 12, 12);
        root.setGravity(Gravity.CENTER_HORIZONTAL);

        TextView header = new TextView(this);
        header.setText("⚡ QUICK BOOK");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 8);
        root.addView(header);

        for (String[] svc : SERVICES) {
            TextView b = new TextView(this);
            b.setText(svc[1] + "  ·  " + svc[2]);
            b.setTextColor(0xFFFFFFFF);
            b.setTextSize(13);
            b.setGravity(Gravity.CENTER);
            b.setBackgroundColor(0xFF14B8A6);
            b.setPadding(8, 10, 8, 10);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = 4;
            b.setLayoutParams(lp);
            b.setClickable(true);
            final String svcId = svc[0];
            b.setOnClickListener(v -> {
                Toast.makeText(this,
                    "Sent to phone: book " + svc[1].substring(svc[1].indexOf(' ') + 1),
                    Toast.LENGTH_SHORT).show();
                // v1.25: send Wearable message to phone-companion APK
                // MessageClient.sendMessage(node, "/servia/quick-book/" + svcId, null);
            });
            root.addView(b);
        }
        setContentView(root);
    }
}
