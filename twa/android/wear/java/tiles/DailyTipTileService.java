package ae.servia.wear.tiles;

import ae.servia.wear.ServiaTheme;

import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.tiles.RequestBuilders;
import java.time.DayOfWeek;
import java.time.LocalDate;

/** Daily tip tile — rotating UAE service tip based on day-of-year. */
public class DailyTipTileService extends ServiaTileBase {
    private static final String[] TIPS = new String[] {
        "Pre-summer: book AC service before May 1 — peak slots fill in 5 days.",
        "Sandstorm season: window cleaning frames + tracks every 3 weeks.",
        "Move-in: deep clean before furniture — saves 40% on labour vs after.",
        "Eid prep: book gardener + pool 1 week ahead, dishes-only maid 2 days.",
        "Pet shedding peak: sofa shampoo every 6 weeks for healthy fabric.",
        "Maid hourly: 3-hour minimum is most cost-efficient slot.",
        "AC duct: do every 2 years, not yearly. UAE filters last that long."
    };

    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
        int idx = LocalDate.now().getDayOfYear() % TIPS.length;
        String tip = TIPS[idx];
        DayOfWeek dow = LocalDate.now().getDayOfWeek();
        return wrap(theme.bg,
            col()
                .addContent(title("💡 SERVIA TIP · " + dow.toString().substring(0, 3), AMBER))
                .addContent(spacer(6))
                .addContent(body(tip, theme.text))
                .addContent(spacer(8))
                .addContent(body("Tap to read full guide", theme.accent))
                .build());
    }
}
