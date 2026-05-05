package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Servia Quick-Book home screen widget.
 *
 * 4×1 strip on the home screen with four tappable service buttons:
 * Deep Cleaning, AC Service, Maid, Handyman. Each tap opens the
 * Servia booking page for that service via a deep-link URL —
 * Android picks the Servia TWA via assetlinks.json verification,
 * so the booking flow opens full-screen inside the installed app.
 */
public class QuickBookWidget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager,
                         int[] appWidgetIds) {
        for (int appWidgetId : appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId);
        }
    }

    private static void updateAppWidget(Context context,
                                        AppWidgetManager mgr,
                                        int widgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_quick_book_widget);
        views.setOnClickPendingIntent(R.id.servia_btn_deep_clean,
                pi(context, "deep_cleaning", widgetId, 1));
        views.setOnClickPendingIntent(R.id.servia_btn_ac,
                pi(context, "ac_cleaning", widgetId, 2));
        views.setOnClickPendingIntent(R.id.servia_btn_maid,
                pi(context, "maid_service", widgetId, 3));
        views.setOnClickPendingIntent(R.id.servia_btn_handyman,
                pi(context, "handyman", widgetId, 4));
        mgr.updateAppWidget(widgetId, views);
    }

    private static PendingIntent pi(Context ctx, String service,
                                    int widgetId, int reqCode) {
        Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(
                "https://servia.ae/book.html?service=" + service +
                "&source=widget"));
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        return PendingIntent.getActivity(ctx, widgetId * 100 + reqCode, i,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }
}
