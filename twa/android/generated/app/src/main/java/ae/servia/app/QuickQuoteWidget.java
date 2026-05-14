package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Quick Quote widget — 2×2 amber tile with "Get a quote" CTA. Tap →
 * /quote.html where user describes their job in free-text and gets an
 * AI-generated price range in seconds. Designed for users who don't
 * know what service category their problem falls under.
 */
public class QuickQuoteWidget extends AppWidgetProvider {
    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_quote_widget);
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(
                "https://servia.ae/quote.html?source=widget"));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            v.setOnClickPendingIntent(R.id.servia_quote_root,
                PendingIntent.getActivity(context, id, i,
                    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
            mgr.updateAppWidget(id, v);
        }
    }
}
