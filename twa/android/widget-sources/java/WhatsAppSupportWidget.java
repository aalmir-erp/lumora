package ae.servia.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * WhatsApp Support widget — 2×1 strip with the WhatsApp green logo.
 * One tap opens wa.me/971XXXXXXXX (the brand support number) so the
 * customer skips the phone book and goes straight to chat. Useful when
 * the user has a problem mid-service and can't open the website.
 */
public class WhatsAppSupportWidget extends AppWidgetProvider {
    private static final String WA_NUMBER = "971507000000";  // brand support

    @Override
    public void onUpdate(Context context, AppWidgetManager mgr, int[] ids) {
        for (int id : ids) {
            RemoteViews v = new RemoteViews(context.getPackageName(),
                                            R.layout.servia_whatsapp_widget);
            String url = "https://wa.me/" + WA_NUMBER +
                "?text=" + Uri.encode("Hi Servia, I need help with");
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            i.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            v.setOnClickPendingIntent(R.id.servia_wa_root,
                PendingIntent.getActivity(context, id, i,
                    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT));
            mgr.updateAppWidget(id, v);
        }
    }
}
