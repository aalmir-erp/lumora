package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * "🛠 All Servia services" wear activity (v1.24.15).
 *
 * Compact 2x2 grid of service icons (8 services total → 2 screens of 4).
 * User scrolls to see them all and taps one to launch SosLauncher with
 * that service_id. The SosLauncher then shows sub-options (issue picker)
 * before capturing GPS and dispatching.
 *
 * Per spec: "show all our services sos small icons 4 in one screen so
 * user can scroll through them and order service from one tile itself".
 */
public class AllServicesActivity extends Activity {

    /** {service_id, emoji, label, color hex without #} */
    private static final String[][] SERVICES = {
        {"vehicle_recovery", "🚗", "Recovery",  "DC2626"},
        {"chauffeur",        "🚙", "Chauffeur", "1D4ED8"},
        {"furniture_move",   "📦", "Move",      "7C3AED"},
        {"handyman",         "🔧", "Handyman",  "16A34A"},
        {"plumber",          "🚿", "Plumber",   "0EA5E9"},
        {"electrician",      "🔌", "Electric",  "FBBF24"},
        {"ac_cleaning",      "❄️", "AC fix",    "06B6D4"},
        {"general_cleaning", "🧹", "Cleaning",  "0F766E"},
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!WearAuth.hasIdentity(this)) {
            Intent onb = new Intent(this, OnboardingActivity.class);
            onb.putExtra("next_class", AllServicesActivity.class.getName());
            startActivity(onb); finish(); return;
        }

        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(8, 16, 8, 12);
        scroll.addView(root);
        setContentView(scroll);

        TextView header = new TextView(this);
        header.setText("🛠 ALL SERVICES");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setTypeface(header.getTypeface(), Typeface.BOLD);
        header.setGravity(Gravity.CENTER);
        header.setPadding(0, 0, 0, 6);
        root.addView(header);

        TextView sub = new TextView(this);
        sub.setText("Tap to dispatch");
        sub.setTextColor(0xFFCBD5E1);
        sub.setTextSize(9);
        sub.setGravity(Gravity.CENTER);
        sub.setPadding(0, 0, 0, 4);
        root.addView(sub);

        // 2x2 grid (we just stack rows of 2 for clarity, scrollable)
        for (int i = 0; i < SERVICES.length; i += 2) {
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.HORIZONTAL);
            LinearLayout.LayoutParams rlp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT);
            rlp.bottomMargin = 6;
            row.setLayoutParams(rlp);

            row.addView(makeCell(SERVICES[i]));
            if (i + 1 < SERVICES.length) row.addView(makeCell(SERVICES[i + 1]));

            root.addView(row);
        }
    }

    private View makeCell(final String[] svc) {
        LinearLayout cell = new LinearLayout(this);
        cell.setOrientation(LinearLayout.VERTICAL);
        cell.setGravity(Gravity.CENTER);
        try { cell.setBackgroundColor((int) Long.parseLong("FF" + svc[3], 16)); }
        catch (Exception e) { cell.setBackgroundColor(0xFFDC2626); }
        cell.setPadding(6, 10, 6, 10);
        LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(
            0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        clp.setMargins(3, 0, 3, 0);
        cell.setLayoutParams(clp);
        cell.setClickable(true);

        TextView ico = new TextView(this);
        ico.setText(svc[1]);
        ico.setTextSize(28);
        ico.setGravity(Gravity.CENTER);
        cell.addView(ico);

        TextView lbl = new TextView(this);
        lbl.setText(svc[2]);
        lbl.setTextColor(0xFFFFFFFF);
        lbl.setTextSize(10);
        lbl.setGravity(Gravity.CENTER);
        lbl.setTypeface(lbl.getTypeface(), Typeface.BOLD);
        cell.addView(lbl);

        cell.setOnClickListener(v -> {
            Intent next = new Intent(this, SosLauncherActivity.class);
            next.putExtra("service_id", svc[0]);
            next.putExtra("category_label", svc[1] + "  " + svc[2]);
            startActivity(next);
        });
        return cell;
    }
}
