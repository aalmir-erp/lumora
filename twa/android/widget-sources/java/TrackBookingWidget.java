package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Servia Track-Booking widget — bigger 4×2 widget that opens the
 * "My account" page where the user sees their active bookings,
 * crew arrival ETA, and live tracking. One tap on the whole widget
 * opens /me.html?source=widget inside the TWA.
 */
public class TrackBookingWidget extends AppWidgetProvider {
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
                                            R.layout.servia_track_widget);
        Intent track = new Intent(Intent.ACTION_VIEW, Uri.parse(
                "https://servia.ae/me.html?source=widget"));
        track.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        PendingIntent piTrack = PendingIntent.getActivity(context,
                widgetId * 200 + 1, track,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        views.setOnClickPendingIntent(R.id.servia_track_root, piTrack);

        Intent book = new Intent(Intent.ACTION_VIEW, Uri.parse(
                "https://servia.ae/book.html?source=widget"));
        book.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        PendingIntent piBook = PendingIntent.getActivity(context,
                widgetId * 200 + 2, book,
                PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        views.setOnClickPendingIntent(R.id.servia_track_book_btn, piBook);

        mgr.updateAppWidget(widgetId, views);
    }
}
