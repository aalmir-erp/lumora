package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Loyalty / Ambassador-tier widget — 2×2 square showing the user's tier
 * (Bronze / Silver / Gold / Platinum), discount % and quick refer link.
 * Tap → /share-rewards.html where they can copy their referral link.
 *
 * Live data not embedded (would need a background sync or app intent
 * service) — the live numbers load when /share-rewards opens.
 */
public class LoyaltyPointsWidget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_loyalty_widget);
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(
                "https://servia.ae/share-rewards.html?source=widget"));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            v.setOnClickPendingIntent(R.id.servia_loyalty_root,
                PendingIntent.getActivity(context, id, i,
                    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
            mgr.updateAppWidget(id, v);
        }
    }
}
