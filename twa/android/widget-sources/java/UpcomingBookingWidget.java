package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Upcoming-booking 4×2 widget.
 *
 * Tapping anywhere opens /me.html where the user sees their next scheduled
 * visit + crew ETA. Visually a card with "NEXT VISIT" eyebrow, body
 * placeholder text (live data fetched when /me opens — widgets can't make
 * background HTTP calls without significant work), and a "Reschedule"
 * pill in the corner. Pin the customer to keep the next-visit context
 * always one tap away.
 */
public class UpcomingBookingWidget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_upcoming_widget);
            v.setOnClickPendingIntent(R.id.servia_upcoming_root,
                openUrl(context, "https://servia.ae/me.html?source=widget", id));
            v.setOnClickPendingIntent(R.id.servia_upcoming_resch,
                openUrl(context, "https://servia.ae/me.html#bookings", id * 100 + 1));
            mgr.updateAppWidget(id, v);
        }
    }
    private static PendingIntent openUrl(Context c, String url, int code) {
        Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
        i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        return PendingIntent.getActivity(c, code, i,
            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }
}
