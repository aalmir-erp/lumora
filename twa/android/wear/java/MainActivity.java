package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

/**
 * Servia Wear OS launcher. v1.24.2 — adds two flagship rows up top:
 *   🎙 Talk  — VoiceAssistantActivity (mic-on-launch chat)
 *   🆘 SOS   — RecoveryActivity (one-tap dispatch)
 * Plus the existing Track / Book / Quote / Chat tiles, all of which now
 * back onto real /api/chat round-trips (no more dummy Toasts).
 */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.wear_main);

        wireTile(R.id.wear_tile_voice,  VoiceAssistantActivity.class);
        wireTile(R.id.wear_tile_sos,    SosCategoryGridActivity.class);  // v1.24.7 — grid with sub-options
        wireTile(R.id.wear_tile_track,  BookingTrackActivity.class);
        wireTile(R.id.wear_tile_book,   QuickBookActivity.class);
        wireTile(R.id.wear_tile_quote,  QuoteActivity.class);
        wireTile(R.id.wear_tile_chat,   ChatActivity.class);
        // v1.24.29 — custom SOS creation + my address + my SOS shortcuts
        wireTile(R.id.wear_tile_create_sos, CustomSosCreateActivity.class);
        wireTile(R.id.wear_tile_address,    LocationActivity.class);
        wireTile(R.id.wear_tile_mysos,      MySosActivity.class);
    }

    private void wireTile(int id, final Class<?> activityClass) {
        View v = findViewById(id);
        if (v == null) return;
        v.setOnClickListener(view -> {
            try {
                startActivity(new Intent(this, activityClass));
            } catch (Exception e) {
                Toast.makeText(this, "Could not open: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
