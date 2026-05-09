# Patch 06 — Admin AI Arena Wins (single source of truth for chat model)

This patch makes the chat-model selection **always** respect what's saved in
the admin panel's AI Arena → Default model per persona, regardless of what
env vars are set on Railway.

## What it changes

`app/main.py` chat priority logic — replaces the old `if settings.use_llm
and (default starts with anthropic OR is empty)` with a clearer rule:

```python
_use_anthropic_primary = (
    _cust_default.startswith("anthropic/") or
    (not _cust_default and not _other_keys_set)
)
```

In plain English:
- If admin set the customer dropdown to `google/gemini-*` → uses Gemini
- If admin set it to `openai/gpt-4o-mini` → uses OpenAI
- If admin set it to `anthropic/claude-haiku-*` → uses Anthropic Haiku
- If admin set it explicitly empty AND has any non-Anthropic key configured → uses cascade
- If admin set nothing AND has zero non-Anthropic keys → uses Railway's `ANTHROPIC_API_KEY` (sane fallback for fresh installs)

So you no longer need to delete `ANTHROPIC_API_KEY` from Railway. The
admin AI Arena UI is the single source of truth.

The patch also adds a log line on every chat request so you can verify
which path was chosen by reading Railway logs:

```
[chat] route=admin-router (admin_default='google/gemini-2.5-flash', other_keys_set=True)
```

## ⚠ This patch contains main.py changes from patches 04 + 05 too

`main.py` was modified by patches 04 (referer parsing) and 05 (admin-live
router). Rather than ship 3 separate main.py hunks that conflict on apply,
patch 06 contains the **complete** main.py state.

**Apply order**:
```bash
git apply 04-traffic-source-parsing.patch       # NOTE: skip its main.py hunks (or apply --reject and discard)
git apply 05-admin-live-pwa.patch               # same — main.py hunks already in 06
git apply 06-admin-ai-arena-wins.patch          # this sets main.py to final state
git add -A && git commit -m "feat: AI Arena always wins + traffic source + admin live PWA"
git push origin main
```

**Easier order** (recommended):
```bash
# Apply only the non-main.py parts of 04 and 05:
git apply --include='app/live_visitors.py' 04-traffic-source-parsing.patch
git apply --include='app/admin_live.py' --include='web/admin-live*' 05-admin-live-pwa.patch
# Then apply the consolidated main.py:
git apply 06-admin-ai-arena-wins.patch
git add -A && git commit -m "feat: chat model is now admin-configured + traffic source + admin live PWA"
git push origin main
```

## After applying

1. Open `https://servia.ae/admin.html` → AI Arena
2. Confirm Gemini API key is filled
3. Set **Customer** dropdown to `google/gemini-2.5-flash` (or whichever)
4. Tap **💾 Save keys + defaults**
5. Wait for Railway redeploy
6. Test chat — Railway logs will show `route=admin-router`
7. Cost on next chat reply: **$0** (Gemini Flash free tier)

## Rollback

If something goes wrong, just delete the saved customer default from admin
AI Arena → Save (empty). The code falls back to Anthropic via Railway env
just like before. Zero state to clean up.
