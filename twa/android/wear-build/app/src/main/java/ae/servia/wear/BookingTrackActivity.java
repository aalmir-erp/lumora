package ae.servia.wear;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup.LayoutParams;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Booking-track screen — native UI, no browser. v1.24.0 stub. */
public class BookingTrackActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(0xFF0F172A);
        root.setPadding(20, 20, 20, 20);
        root.setLayoutParams(new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT));

        TextView header = new TextView(this);
        header.setText("📋 BOOKINGS");
        header.setTextColor(0xFFFCD34D);
        header.setTextSize(11);
        header.setGravity(Gravity.CENTER);
        root.addView(header);

        TextView empty = new TextView(this);
        empty.setText("No bookings yet.\nOpen the Servia app on your phone to book.");
        empty.setTextColor(0xFFE2E8F0);
        empty.setTextSize(13);
        empty.setGravity(Gravity.CENTER);
        empty.setPadding(0, 12, 0, 12);
        root.addView(empty);

        TextView hint = new TextView(this);
        hint.setText("Watch syncs from phone in v1.25");
        hint.setTextColor(0xFF94A3B8);
        hint.setTextSize(10);
        hint.setGravity(Gravity.CENTER);
        root.addView(hint);

        setContentView(root);
    }
}
