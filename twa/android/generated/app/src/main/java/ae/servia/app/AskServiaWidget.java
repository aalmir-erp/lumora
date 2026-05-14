package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Ask Servia widget — 4×2 chat-style card with the Servia mascot avatar
 * and a quick prompt ("Hey! Tap to ask anything"). Below the prompt are
 * three tap-zones: Book / Quote / Track. Tap the body or any of the
 * three → opens the matching servia.ae page with the chat panel
 * auto-opened (?chat=1) so the user can type their question + place
 * an order in one flow.
 */
public class AskServiaWidget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_ask_widget);
            v.setOnClickPendingIntent(R.id.servia_ask_root,
                openUrl(context, "https://servia.ae/?chat=1&source=widget", id * 100));
            v.setOnClickPendingIntent(R.id.servia_ask_book,
                openUrl(context, "https://servia.ae/book.html?source=widget", id * 100 + 1));
            v.setOnClickPendingIntent(R.id.servia_ask_quote,
                openUrl(context, "https://servia.ae/quote.html?source=widget", id * 100 + 2));
            v.setOnClickPendingIntent(R.id.servia_ask_track,
                openUrl(context, "https://servia.ae/me.html?source=widget", id * 100 + 3));
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
