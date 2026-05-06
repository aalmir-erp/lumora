package ae.servia.wear;

import android.util.Log;
import com.google.android.gms.wearable.MessageEvent;
import com.google.android.gms.wearable.WearableListenerService;

/**
 * Listens for Wearable Data Layer messages from the paired phone.
 *
 * Phone-side TWA can't directly publish to the Data Layer (TWAs are
 * Chrome custom-tabs and don't have wearable APIs). For phone↔watch
 * sync we'll add a tiny native phone-companion APK in v1.25 that bridges:
 *
 *   /servia/booking-update  → push next booking ETA + status to tiles
 *   /servia/wallet-update   → push wallet balance to WalletTileService
 *   /servia/loyalty-update  → push tier change to LoyaltyTileService
 *
 * Until then this service is a stub that logs incoming messages.
 */
public class WearMessageListenerService extends WearableListenerService {

    private static final String TAG = "ServiaWear";

    @Override
    public void onMessageReceived(MessageEvent ev) {
        Log.i(TAG, "msg path=" + ev.getPath() + " from=" + ev.getSourceNodeId());
        // TODO v1.25: route by path → SharedPrefs → trigger tile refresh
        super.onMessageReceived(ev);
    }
}
