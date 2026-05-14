package ae.servia.wear;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;

/**
 * v1.24.43 — fallback opener used when the watch can't open
 * https://servia.ae directly (no browser installed). On modern Wear OS
 * this almost always works via {@code Intent.ACTION_VIEW} + Chrome, but
 * standalone watches without WiFi lose the browser. We fall back to
 * showing a Toast prompting the user to open the URL on their phone.
 *
 * Future: extend with a Wearable Data Layer message that pings the
 * paired phone to open the URL in its browser.
 */
public final class WatchHomepageBridge {
    private WatchHomepageBridge() {}

    public static void openOnPhone(Context ctx) {
        try {
            Toast.makeText(ctx, "Open servia.ae on your phone",
                           Toast.LENGTH_LONG).show();
        } catch (Throwable ignored) {}
    }

    /** Try direct intent first; toast fallback. */
    public static boolean openHomepage(Context ctx) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse("https://servia.ae"));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            ctx.startActivity(i);
            return true;
        } catch (Throwable t) {
            openOnPhone(ctx);
            return false;
        }
    }
}
