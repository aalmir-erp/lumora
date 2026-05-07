package ae.servia.wear.tiles;

import ae.servia.wear.ServiaTheme;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/**
 * Servia voice-assistant tile (v1.24.2). One big yellow tap target.
 *
 * Tap → launches VoiceAssistantActivity which immediately opens the
 * watch microphone. Speak your booking ("book a deep clean tomorrow"),
 * Servia replies in voice + text, calls create_booking under the hood,
 * and shows a green confirmation chip with the booking id.
 *
 * This is the tile users add first — it does book / quote / chat /
 * recovery / wallet all by talking, so they don't have to remember
 * which tile does what.
 */
public class ServiaVoiceTileService extends ServiaTileBase {
    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(RequestBuilders.TileRequest req) {
        ServiaTheme theme = ServiaTheme.current(this);
        ModifiersBuilders.Clickable launch =
            new ModifiersBuilders.Clickable.Builder()
                .setId("servia_voice")
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName("ae.servia.wear.VoiceAssistantActivity")
                                .build())
                        .build())
                .build();

        return new LayoutElementBuilders.Box.Builder()
            .setWidth(DimensionBuilders.expand())
            .setHeight(DimensionBuilders.expand())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
            .setModifiers(
                new ModifiersBuilders.Modifiers.Builder()
                    .setBackground(
                        new ModifiersBuilders.Background.Builder()
                            .setColor(ColorBuilders.argb(theme.primary))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(20))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(12))
                            .build())
                    .setClickable(launch)
                    .build())
            .addContent(
                col()
                    .addContent(title("🎙 SERVIA", DARK))
                    .addContent(spacer(4))
                    .addContent(big("TALK", DARK))
                    .addContent(spacer(2))
                    .addContent(body("Speak: book · quote · recovery · wallet", DARK))
                    .addContent(spacer(6))
                    .addContent(body("Voice answers + real bookings", theme.text))
                    .build())
            .build();
    }
}
