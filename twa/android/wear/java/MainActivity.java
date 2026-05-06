package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

/**
 * Servia Wear OS main launcher activity.
 *
 * v1.24.0 — Rewrites the previous browser-launch design (which produced
 * unusable tiny web pages on the watch). Now each tile in the launcher
 * goes to a dedicated SCREEN ACTIVITY:
 *
 *   wear_tile_track  → BookingTrackActivity   (native list of bookings)
 *   wear_tile_book   → QuickBookActivity      (4 service buttons → tap to send)
 *   wear_tile_quote  → QuoteActivity          (numeric AED estimate)
 *   wear_tile_chat   → ChatActivity           (voice-input quick-message)
 *
 * The actual booking submit / quote calculation / chat send is forwarded
 * to the paired phone via the Wearable Data Layer (Phone-side message
 * listener forwards to /api/* over HTTPS). Watch never opens a browser.
 *
 * Until the phone-companion APK lands in v1.25, the secondary screens
 * show a "Use phone app to complete" prompt instead of crashing.
 */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.wear_main);

        wireTile(R.id.wear_tile_track,  BookingTrackActivity.class);
        wireTile(R.id.wear_tile_book,   QuickBookActivity.class);
        wireTile(R.id.wear_tile_quote,  QuoteActivity.class);
        wireTile(R.id.wear_tile_chat,   ChatActivity.class);
    }

    private void wireTile(int id, final Class<?> activityClass) {
        View v = findViewById(id);
        if (v == null) return;
        v.setOnClickListener(view -> {
            try {
                startActivity(new Intent(this, activityClass));
            } catch (Exception e) {
                Toast.makeText(this, "Use the phone app", Toast.LENGTH_SHORT).show();
            }
        });
    }
}
