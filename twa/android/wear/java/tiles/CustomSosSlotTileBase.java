package ae.servia.wear.tiles;

import android.content.SharedPreferences;

import androidx.wear.protolayout.ActionBuilders;
import androidx.wear.protolayout.ColorBuilders;
import androidx.wear.protolayout.DimensionBuilders;
import androidx.wear.protolayout.LayoutElementBuilders;
import androidx.wear.protolayout.ModifiersBuilders;
import androidx.wear.tiles.RequestBuilders;

/**
 * v1.24.29 — base class for the 5 pre-registered "Custom SOS Slot"
 * tiles. Each subclass returns its slot number (1..5). Tiles read
 * SharedPreferences ("servia_csos_slots") to find which custom
 * shortcut the user has bound to this slot.
 *
 *   - bound:    big label + "TAP TO SOS" → launches
 *               CustomSosSlotDispatchActivity with the slot number,
 *               which POSTs /api/sos/custom/{id}/dispatch.
 *   - unbound:  "EMPTY · Tap to create" → launches
 *               CustomSosCreateActivity.
 *
 * Five slots is the right balance: enough for the most common
 * scenarios (home, parents, office, car, friend) without spamming
 * the tile picker.
 */
public abstract class CustomSosSlotTileBase extends ServiaTileBase {

    /** Subclasses return 1..5. */
    protected abstract int slotNumber();

    @Override
    protected LayoutElementBuilders.LayoutElement buildLayout(
            RequestBuilders.TileRequest req) {

        SharedPreferences sp = getSharedPreferences(
            "servia_csos_slots", MODE_PRIVATE);
        int btnId = sp.getInt("csos_slot_" + slotNumber() + "_id", 0);
        String label = sp.getString(
            "csos_slot_" + slotNumber() + "_label", null);
        String emoji = sp.getString(
            "csos_slot_" + slotNumber() + "_emoji", "🆘");

        boolean bound = btnId > 0 && label != null;

        ModifiersBuilders.Clickable click;
        if (bound) {
            click = new ModifiersBuilders.Clickable.Builder()
                .setId("csos_slot_" + slotNumber())
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName(
                                    "ae.servia.wear.CustomSosSlotDispatchActivity")
                                .addKeyToExtraMapping(
                                    "slot",
                                    new ActionBuilders.AndroidIntExtra.Builder()
                                        .setValue(slotNumber())
                                        .build())
                                .build())
                        .build())
                .build();
        } else {
            click = new ModifiersBuilders.Clickable.Builder()
                .setId("csos_slot_create_" + slotNumber())
                .setOnClick(
                    new ActionBuilders.LaunchAction.Builder()
                        .setAndroidActivity(
                            new ActionBuilders.AndroidActivity.Builder()
                                .setPackageName("ae.servia.wear")
                                .setClassName(
                                    "ae.servia.wear.CustomSosCreateActivity")
                                .build())
                        .build())
                .build();
        }

        LayoutElementBuilders.Column.Builder content = col();
        if (bound) {
            content.addContent(title("⚡ SLOT " + slotNumber(), AMBER))
                   .addContent(spacer(4))
                   .addContent(big(emoji, WHITE))
                   .addContent(spacer(2))
                   .addContent(body(label, WHITE))
                   .addContent(spacer(6))
                   .addContent(body("Tap → SOS", AMBER));
        } else {
            content.addContent(title("⚡ SLOT " + slotNumber(), AMBER))
                   .addContent(spacer(6))
                   .addContent(big("+", WHITE))
                   .addContent(spacer(4))
                   .addContent(body("Empty · tap to\ncreate shortcut", WHITE));
        }

        return new LayoutElementBuilders.Box.Builder()
            .setWidth(DimensionBuilders.expand())
            .setHeight(DimensionBuilders.expand())
            .setHorizontalAlignment(LayoutElementBuilders.HORIZONTAL_ALIGN_CENTER)
            .setVerticalAlignment(LayoutElementBuilders.VERTICAL_ALIGN_CENTER)
            .setModifiers(
                new ModifiersBuilders.Modifiers.Builder()
                    .setBackground(
                        new ModifiersBuilders.Background.Builder()
                            .setColor(ColorBuilders.argb(
                                bound ? RED : 0xFF334155))
                            .setCorner(
                                new ModifiersBuilders.Corner.Builder()
                                    .setRadius(DimensionBuilders.dp(20))
                                    .build())
                            .build())
                    .setPadding(
                        new ModifiersBuilders.Padding.Builder()
                            .setAll(DimensionBuilders.dp(12))
                            .build())
                    .setClickable(click)
                    .build())
            .addContent(content.build())
            .build();
    }
}
