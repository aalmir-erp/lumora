package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;
import java.util.Calendar;

/**
 * Daily Tip widget — 4×2 card that rotates one UAE-relevant home-services
 * tip per day. Tapping it opens /blog where the user can read the
 * source article. Tip text is selected client-side based on day-of-year
 * so it changes each day without needing background sync.
 */
public class DailyTipWidget extends AppWidgetProvider {
    private static final String[] TIPS = {
        "🌬 Pre-summer AC: clean the filters every 30 days. Saves 15% on cooling bills.",
        "🧹 Marble polish: every 6 months in Dubai (sand storms dull it fast).",
        "🪲 Cockroaches travel in pairs. Treat the kitchen + bathroom in one visit.",
        "❄️ AC dripping water? 90% of the time it's a clogged drain pan. 30 min fix.",
        "📦 Move-out cleaning: book deep + steam carpets together for the security deposit.",
        "🛋 Sofa stains older than 24h need enzyme treatment, not just shampoo.",
        "💧 Water tank cleaning every 6 months (UAE Municipality requirement in some areas).",
        "🍳 Kitchen exhaust hood: scrub monthly or it becomes a fire risk.",
        "🚿 Showerhead descaling: vinegar overnight beats expensive limescale removers.",
        "🌅 Best time to book deep cleaning: weekday morning. Crews are 30% faster (less Marina traffic).",
    };

    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        Calendar cal = Calendar.getInstance();
        int dayOfYear = cal.get(Calendar.DAY_OF_YEAR);
        String tip = TIPS[dayOfYear % TIPS.length];
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_dailytip_widget);
            v.setTextViewText(R.id.servia_tip_text, tip);
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(
                "https://servia.ae/blog?source=widget"));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            v.setOnClickPendingIntent(R.id.servia_tip_root,
                PendingIntent.getActivity(context, id, i,
                    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
            mgr.updateAppWidget(id, v);
        }
    }
}
