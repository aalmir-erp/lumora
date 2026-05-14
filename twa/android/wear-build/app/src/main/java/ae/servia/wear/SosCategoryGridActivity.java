package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * Servia SOS category grid (v1.24.7) — mirrors the website /sos.html's
 * 8-tile launcher on the watch. Tapping the launcher's red SOS button or
 * the SOS-Recovery tile no longer dispatches a vehicle truck blindly;
 * it opens this screen, which lets the user pick the kind of help, then
 * launches SosLauncherActivity with the right service_id (which then
 * shows the issue sub-options before capturing GPS).
 *
 * Each row is a tappable card: emoji + bold name + 11sp sub-text.
 * Vehicle and Chauffeur are flagged "24/7 urgent" (red top-row pair).
 * Other categories follow.
 *
 * Vertical ScrollView so small round screens still scroll the full set.
 */
public class SosCategoryGridActivity extends Activity {

    /** {service_id, emoji, name, sub, urgent? "1":"0", color int as hex string} */
    private static final String[][] CATS = {
        {"vehicle_recovery", "🚗", "Vehicle recovery", "Tow · battery · tyre",  "1", "DC2626"},
        {"chauffeur",        "🚙", "Chauffeur",        "Driver · airport",      "1", "DC2626"},
        {"furniture_move",   "📦", "Furniture",        "Move · assemble · fix", "0", "7C3AED"},
        {"handyman",         "🔧", "Handyman",         "Paint · door · curtains","0", "16A34A"},
        {"plumber",          "🚿", "Plumber",          "Leak · clog · install", "0", "0EA5E9"},
        {"electrician",      "🔌", "Electrician",      "No power · install",    "0", "FBBF24"},
        {"ac_cleaning",      "❄️", "AC fix / clean",   "Not cooling · gas",     "0", "06B6D4"},
        {"general_cleaning", "🧹", "Cleaning",         "General · deep · maid", "0", "0F766E"},
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Onboarding gate so the first dispatch is bound to a real customer.
        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", SosCategoryGridActivity.class.getName());
            startActivity(onb);
            finish();
            return;
        }

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF7F1D1D);
        root.setPadding(10, 18, 10, 14);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("🆘 SERVIA QUICK SERVICE");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 4);
        root.addView(header);

        TextView sub = new TextView(this);
        sub.setText("One-tap dispatch · real GPS · 24/7");
        sub.setTextColor(0xFFFEE2E2);
        sub.setTextSize(9);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 0, 0, 8);
        root.addView(sub);

        for (final String[] cat : CATS) {
            final boolean urgent = "1".equals(cat[4]);
            int bg = urgent ? 0xFFDC2626 : 0xFFFFFFFF;
            int fg = urgent ? 0xFFFFFFFF : 0xFF0F172A;
            int subFg = urgent ? 0xFFFEE2E2 : 0xFF475569;

            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundColor(bg);
            card.setPadding(12, 10, 12, 10);
            LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
            clp.bottomMargin = 8;
            card.setLayoutParams(clp);
            card.setClickable(true);

            TextView ico = new TextView(this);
            ico.setText(cat[1]);
            ico.setTextSize(22);
            card.addView(ico);

            TextView name = new TextView(this);
            name.setText(cat[2]);
            name.setTextColor(fg);
            name.setTextSize(13);
            name.setTypeface(name.getTypeface(), Typeface.BOLD);
            card.addView(name);

            TextView sb = new TextView(this);
            sb.setText(cat[3]);
            sb.setTextColor(subFg);
            sb.setTextSize(10);
            card.addView(sb);

            if (urgent) {
                TextView badge = new TextView(this);
                badge.setText("24/7");
                badge.setTextColor(0xFF7C2D12);
                badge.setBackgroundColor(0xFFFCD34D);
                badge.setTextSize(8);
                badge.setTypeface(badge.getTypeface(), Typeface.BOLD);
                badge.setPadding(6, 1, 6, 1);
                LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT);
                blp.topMargin = 4;
                badge.setLayoutParams(blp);
                card.addView(badge);
            }

            card.setOnClickListener(v -> {
                Intent next = new Intent(this, SosLauncherActivity.class);
                next.putExtra("service_id", cat[0]);
                next.putExtra("category_label", cat[1] + "  " + cat[2]);
                startActivity(next);
            });
            root.addView(card);
        }

        // "How does this work?" footer
        TextView help = new TextView(this);
        help.setText("Pick a service → choose what kind → confirm location → "
                   + "we send GPS + dispatch closest pro.");
        help.setTextColor(0xFFFCA5A5);
        help.setTextSize(9);
        help.setGravity(Gravity.CENTER);
        help.setPadding(4, 8, 4, 8);
        root.addView(help);
    }
}
