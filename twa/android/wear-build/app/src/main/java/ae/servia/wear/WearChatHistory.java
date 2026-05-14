package ae.servia.wear;

import java.util.ArrayList;
import java.util.List;

/**
 * Process-wide chat history. Stays alive while the wear app process is
 * alive, so going back to MainActivity and re-opening Chat shows the
 * full conversation again instead of starting fresh.
 *
 * Cleared explicitly via {@link #clear()} (e.g. user taps "New chat"
 * or onboarding logs out).
 */
public final class WearChatHistory {
    public enum Side { USER, SERVIA, CHIP }
    public static final class Bubble {
        public final Side side;
        public final String text;
        public Bubble(Side s, String t) { side = s; text = t; }
    }
    private static final List<Bubble> BUBBLES = new ArrayList<>();
    private WearChatHistory() {}
    public static synchronized void add(Side s, String t) { BUBBLES.add(new Bubble(s, t)); }
    public static synchronized List<Bubble> snapshot() { return new ArrayList<>(BUBBLES); }
    public static synchronized void clear() { BUBBLES.clear(); WearApi.sessionId = null; }
    public static synchronized boolean isEmpty() { return BUBBLES.isEmpty(); }
}
