package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Search widget — 4×1 strip that looks like a search bar (magnifying
 * glass + 'Search Servia services, areas, FAQs…' placeholder + voice mic
 * icon). Tap → opens https://servia.ae/search.html where the full search
 * UI takes over (live suggestions, voice, AI mode, recent queries).
 *
 * The mic icon end-of-bar opens search?voice=1 which auto-triggers the
 * Web Speech API on landing — one-tap voice search.
 */
public class SearchWidget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_search_widget);
            v.setOnClickPendingIntent(R.id.servia_search_root,
                openUrl(context, "https://servia.ae/search.html?source=widget", id));
            v.setOnClickPendingIntent(R.id.servia_search_mic,
                openUrl(context, "https://servia.ae/search.html?voice=1&source=widget", id * 100 + 1));
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
