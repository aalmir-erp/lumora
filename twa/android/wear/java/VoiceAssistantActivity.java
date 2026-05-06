package ae.servia.wear;

/**
 * Servia voice assistant — same as ChatActivity but the mic opens the
 * moment the activity loads, so the user can just tap the tile and
 * start talking. Used by the unified "🎙 SERVIA" tile.
 */
public class VoiceAssistantActivity extends ChatActivity {
    @Override
    protected boolean autoOpenMic() { return true; }

    @Override
    protected String micPrompt() { return "Speak — book, quote, recovery, wallet…"; }
}
