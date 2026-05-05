package ae.servia.wear;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Servia Wear OS standalone activity.
 *
 * 4 large tappable tiles for the most-used flows:
 *   1. Track booking → opens https://servia.ae/me.html on the watch's
 *      browser if available, otherwise mirrors the intent to the paired
 *      phone (Wear OS auto-mirrors VIEW intents).
 *   2. Quick book → opens /book.html
 *   3. Talk to Servia → opens chat
 *   4. Quote → opens /quote.html
 *
 * No external dependencies — single Activity with a programmatically-
 * built BoxInsetLayout. Builds against the wearable support library and
 * runs on any Wear OS 2.0+ watch as a standalone APK.
 */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.wear_main);

        wireTile(R.id.wear_tile_track,
                 "https://servia.ae/me.html?source=wear");
        wireTile(R.id.wear_tile_book,
                 "https://servia.ae/book.html?source=wear");
        wireTile(R.id.wear_tile_quote,
                 "https://servia.ae/quote.html?source=wear");
        wireTile(R.id.wear_tile_chat,
                 "https://servia.ae/?chat=1&source=wear");
    }

    private void wireTile(int id, final String url) {
        View v = findViewById(id);
        if (v == null) return;
        v.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                try {
                    startActivity(intent);
                } catch (Exception e) {
                    // Wear OS will auto-forward unhandled VIEW intents to the
                    // paired phone via the Companion app, so silent-fail is OK.
                }
            }
        });
    }
}
