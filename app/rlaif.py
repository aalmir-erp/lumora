"""v1.24.134 — RLAIF feedback loop for the Servia chatbot.

WHAT
----
Continuous improvement loop for AI chat replies. Two feedback signals:
  1. HUMAN (RLHF-style): customer clicks 👍/👎 after a reply,
     optionally adds a reason tag + free-text.
  2. AI CRITIC (RLAIF-style): a separate Claude/GPT call scores each
     reply against a rubric {accurate, on-brand, tool-correct, helpful,
     concise}. The critic runs on-demand or on a schedule and flags any
     reply scoring < 6/10 average.

Both signals feed into:
  - An admin review queue (low-scoring replies surface for inspection)
  - Aggregate metrics (booking-completion correlation, score trends)
  - Future: automated few-shot example promotion (good replies become
    in-context examples on the next prompt iteration)

WHY THIS IS NOT TRUE RLHF
-------------------------
True RLHF requires access to model weights (Anthropic doesn't expose
Claude's weights). What we run is the closest practical equivalent:
prompt evolution driven by collected feedback. The bot gets measurably
better week-over-week without us training anything; we tune the prompt
+ few-shot examples + model routing instead.

TABLES
------
  chat_feedback     — human thumbs + reason on a specific reply
  critic_scores     — AI critic's per-dimension score on a reply

EXTENDING
---------
- Add a new reason tag: extend REASON_TAGS below. Validated server-side.
- Add a new rubric dimension: extend RUBRIC_DIMENSIONS. The critic
  prompt auto-includes it.
- Promote a good reply to a few-shot example: separate
  /api/admin/feedback/{id}/promote endpoint stores it in cfg under
  key "chat.fewshot_examples" — your system prompt builder reads that.

ROUTES
------
  POST /api/chat/feedback           public, customer-submitted thumbs
  GET  /api/admin/feedback/queue    admin, low-scoring or flagged items
  GET  /api/admin/feedback/stats    admin, aggregate metrics
  POST /api/admin/critic/run        admin, trigger critic batch
  POST /api/admin/feedback/{id}/dismiss   admin, reviewed
  POST /api/admin/feedback/{id}/promote   admin, promote to few-shot
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from . import db
from .auth import require_admin


router = APIRouter()


# Allowed reason tags for thumbs-down. Validated server-side so the UI
# can't smuggle in arbitrary strings (avoids junk in analytics).
REASON_TAGS = {
    "wrong_price",         # bot quoted a wrong AED amount
    "off_brand_tone",      # too formal/casual/aggressive for Servia voice
    "missed_context",      # bot forgot something said earlier
    "tool_failed",         # bot tried to book/quote but the tool didn't fire
    "too_long",            # over-explained, lost user attention
    "too_short",           # dropped a question that needed a real answer
    "wrong_language",      # replied in EN when user wrote in AR / vice-versa
    "factually_wrong",     # claim contradicts our actual service
    "other",
}


# Rubric the critic agent scores each reply against. Each 0-10.
# Average across dimensions = the reply's "quality score".
RUBRIC_DIMENSIONS = {
    "accurate":      "Is every factual claim true? (pricing, service details, "
                     "policies). 0 = contains a clear error, 10 = nothing wrong.",
    "on_brand":      "Does it sound like Servia's voice (warm, direct, no fluff, "
                     "no aggressive sales)? 0 = totally off-brand, 10 = perfect fit.",
    "tool_correct":  "If a tool was needed (book, quote, lookup), was the right "
                     "tool called with the right args? If no tool needed, 10.",
    "helpful":       "Does it move the customer forward? 0 = wastes their time, "
                     "10 = clearly resolves or advances.",
    "concise":       "Right length for the question? 0 = obvious padding or "
                     "way too brief, 10 = exactly right.",
}


# ─────────────────────────────────────────────────────────────────────
# Schema bootstrap — runs at import (mirrors nfc.py pattern)
# ─────────────────────────────────────────────────────────────────────
def _init_schema() -> None:
    with db.connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_feedback (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            message_id      INTEGER,           -- conversations.id if known
            rating          INTEGER NOT NULL,  -- +1 (thumbs up) or -1 (thumbs down)
            reason_tag      TEXT,              -- one of REASON_TAGS, or NULL
            reason_text     TEXT,              -- free-text explanation
            prompt_text     TEXT,              -- what the user asked (snapshot)
            response_text   TEXT,              -- what the bot replied (snapshot)
            model_used      TEXT,              -- provider/model that generated it
            tools_called    TEXT,              -- JSON list of tool names called
            customer_id     INTEGER,           -- customers.id if logged in
            ip              TEXT,
            user_agent      TEXT,
            reviewed_at     TEXT,              -- admin marked as reviewed (NULL = pending)
            reviewed_by     TEXT,              -- admin token id or 'auto-dismissed'
            promoted_to_fewshot INTEGER DEFAULT 0,  -- admin promoted as example
            created_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_cf_session ON chat_feedback(session_id);
        CREATE INDEX IF NOT EXISTS idx_cf_rating ON chat_feedback(rating);
        CREATE INDEX IF NOT EXISTS idx_cf_reviewed ON chat_feedback(reviewed_at);
        CREATE INDEX IF NOT EXISTS idx_cf_created ON chat_feedback(created_at);

        CREATE TABLE IF NOT EXISTS critic_scores (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id      INTEGER,           -- conversations.id
            session_id      TEXT NOT NULL,
            prompt_text     TEXT,              -- user's prompt (snapshot)
            response_text   TEXT,              -- bot's reply (snapshot)
            model_used      TEXT,              -- which model produced the reply
            scores_json     TEXT NOT NULL,     -- {accurate:8, on_brand:7, ...}
            avg_score       REAL NOT NULL,     -- average across dimensions
            critic_notes    TEXT,              -- critic's free-text rationale
            critic_model    TEXT,              -- which model ran the critique
            flagged         INTEGER DEFAULT 0, -- avg_score < 6 → 1
            reviewed_at     TEXT,
            created_at      TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_cs_session ON critic_scores(session_id);
        CREATE INDEX IF NOT EXISTS idx_cs_flagged ON critic_scores(flagged);
        CREATE INDEX IF NOT EXISTS idx_cs_avg ON critic_scores(avg_score);
        CREATE INDEX IF NOT EXISTS idx_cs_created ON critic_scores(created_at);
        """)


_init_schema()


# ─────────────────────────────────────────────────────────────────────
# Customer-facing: submit thumbs feedback
# ─────────────────────────────────────────────────────────────────────
class FeedbackBody(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    message_id: Optional[int] = None
    rating: int = Field(..., ge=-1, le=1)  # -1, 0, +1
    reason_tag: Optional[str] = None
    reason_text: Optional[str] = Field(None, max_length=2000)
    prompt_text: Optional[str] = Field(None, max_length=8000)
    response_text: Optional[str] = Field(None, max_length=16000)
    model_used: Optional[str] = None
    tools_called: Optional[list[str]] = None


@router.post("/api/chat/feedback")
def submit_feedback(body: FeedbackBody, request: Request):
    """Customer-facing thumbs endpoint. Always returns 200 (we never want
    to break the chat UI if feedback collection fails server-side).
    Rate-limit-friendly: dedup on (session_id, message_id) by upserting."""
    if body.rating == 0:
        # Rating 0 = user retracted; we delete prior feedback for this msg.
        try:
            with db.connect() as c:
                c.execute(
                    "DELETE FROM chat_feedback WHERE session_id=? AND message_id=?",
                    (body.session_id, body.message_id))
        except Exception:
            pass
        return {"ok": True, "action": "retracted"}

    if body.reason_tag and body.reason_tag not in REASON_TAGS:
        body.reason_tag = "other"

    try:
        with db.connect() as c:
            # Upsert: one row per (session, message_id). If user changes
            # mind from 👎 to 👍, the row gets updated.
            existing = None
            if body.message_id is not None:
                row = c.execute(
                    "SELECT id FROM chat_feedback WHERE session_id=? AND message_id=?",
                    (body.session_id, body.message_id)).fetchone()
                if row:
                    existing = row["id"]
            now = datetime.now(timezone.utc).isoformat()
            ip = (request.client.host if request.client else None) or ""
            ua = (request.headers.get("user-agent") or "")[:300]
            if existing:
                c.execute("""
                    UPDATE chat_feedback
                    SET rating=?, reason_tag=?, reason_text=?, prompt_text=?,
                        response_text=?, model_used=?, tools_called=?,
                        ip=?, user_agent=?
                    WHERE id=?
                """, (body.rating, body.reason_tag, body.reason_text,
                      body.prompt_text, body.response_text, body.model_used,
                      json.dumps(body.tools_called or []), ip, ua, existing))
            else:
                c.execute("""
                    INSERT INTO chat_feedback
                      (session_id, message_id, rating, reason_tag, reason_text,
                       prompt_text, response_text, model_used, tools_called,
                       ip, user_agent, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (body.session_id, body.message_id, body.rating,
                      body.reason_tag, body.reason_text, body.prompt_text,
                      body.response_text, body.model_used,
                      json.dumps(body.tools_called or []),
                      ip, ua, now))
            return {"ok": True, "action": "stored"}
    except Exception as e:
        # Never break the chat UI — just log and return ok.
        print(f"[rlaif] feedback store failed: {e}", flush=True)
        return {"ok": True, "action": "skipped_error"}


# ─────────────────────────────────────────────────────────────────────
# Admin: review queue + stats
# ─────────────────────────────────────────────────────────────────────
@router.get("/api/admin/feedback/queue",
            dependencies=[Depends(require_admin)])
def admin_feedback_queue(limit: int = 50, kind: str = "all"):
    """Returns items needing review. kind = thumbs|critic|all.

    Thumbs items: any 👎 not yet reviewed.
    Critic items: any critic score < 6 not yet reviewed.
    """
    items: list[dict] = []
    with db.connect() as c:
        if kind in ("thumbs", "all"):
            rows = c.execute("""
                SELECT id, session_id, message_id, rating, reason_tag,
                       reason_text, prompt_text, response_text, model_used,
                       created_at
                FROM chat_feedback
                WHERE rating = -1 AND reviewed_at IS NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            for r in rows:
                items.append({
                    "kind": "thumbs",
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "message_id": r["message_id"],
                    "reason_tag": r["reason_tag"],
                    "reason_text": r["reason_text"],
                    "prompt_text": r["prompt_text"],
                    "response_text": r["response_text"],
                    "model_used": r["model_used"],
                    "created_at": r["created_at"],
                })
        if kind in ("critic", "all"):
            rows = c.execute("""
                SELECT id, session_id, message_id, scores_json, avg_score,
                       critic_notes, prompt_text, response_text, model_used,
                       critic_model, created_at
                FROM critic_scores
                WHERE flagged = 1 AND reviewed_at IS NULL
                ORDER BY avg_score ASC, created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            for r in rows:
                try:
                    scores = json.loads(r["scores_json"])
                except Exception:
                    scores = {}
                items.append({
                    "kind": "critic",
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "message_id": r["message_id"],
                    "avg_score": r["avg_score"],
                    "scores": scores,
                    "critic_notes": r["critic_notes"],
                    "prompt_text": r["prompt_text"],
                    "response_text": r["response_text"],
                    "model_used": r["model_used"],
                    "critic_model": r["critic_model"],
                    "created_at": r["created_at"],
                })
    return {"ok": True, "count": len(items), "items": items}


@router.get("/api/admin/feedback/stats",
            dependencies=[Depends(require_admin)])
def admin_feedback_stats(days: int = 30):
    """Aggregate metrics — thumbs rate, critic avg, top reason tags."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    out: dict = {"window_days": days}
    with db.connect() as c:
        # Thumbs stats
        rows = c.execute("""
            SELECT
                SUM(CASE WHEN rating= 1 THEN 1 ELSE 0 END) AS up,
                SUM(CASE WHEN rating=-1 THEN 1 ELSE 0 END) AS down,
                COUNT(*) AS total
            FROM chat_feedback
            WHERE created_at >= ?
        """, (cutoff,)).fetchone()
        up = (rows["up"] or 0); down = (rows["down"] or 0); total = (rows["total"] or 0)
        out["thumbs"] = {
            "up": up, "down": down, "total": total,
            "positive_rate": (up / total) if total else None,
        }
        # Top reason tags for thumbs-down
        rows = c.execute("""
            SELECT reason_tag, COUNT(*) AS n FROM chat_feedback
            WHERE rating=-1 AND created_at >= ? AND reason_tag IS NOT NULL
            GROUP BY reason_tag ORDER BY n DESC LIMIT 10
        """, (cutoff,)).fetchall()
        out["top_negative_reasons"] = [{"tag": r["reason_tag"], "count": r["n"]}
                                        for r in rows]
        # Critic stats
        rows = c.execute("""
            SELECT AVG(avg_score) AS avg, COUNT(*) AS total,
                   SUM(CASE WHEN flagged=1 THEN 1 ELSE 0 END) AS flagged
            FROM critic_scores WHERE created_at >= ?
        """, (cutoff,)).fetchone()
        out["critic"] = {
            "scored_replies": (rows["total"] or 0),
            "avg_score": (round(rows["avg"], 2) if rows["avg"] is not None else None),
            "flagged": (rows["flagged"] or 0),
        }
        # Score trend by day (last 14 days)
        rows = c.execute("""
            SELECT date(created_at) AS d, AVG(avg_score) AS avg, COUNT(*) AS n
            FROM critic_scores
            WHERE created_at >= ?
            GROUP BY d ORDER BY d ASC
        """, ((datetime.now(timezone.utc) - timedelta(days=14)).isoformat(),)).fetchall()
        out["critic_trend"] = [{"date": r["d"], "avg": round(r["avg"] or 0, 2),
                                 "count": r["n"]} for r in rows]
    return {"ok": True, **out}


@router.post("/api/admin/feedback/{fb_id}/dismiss",
             dependencies=[Depends(require_admin)])
def admin_dismiss_feedback(fb_id: int, kind: str = "thumbs"):
    """Mark a thumbs-feedback or critic-score as reviewed."""
    table = "chat_feedback" if kind == "thumbs" else "critic_scores"
    now = datetime.now(timezone.utc).isoformat()
    with db.connect() as c:
        c.execute(f"UPDATE {table} SET reviewed_at=?, reviewed_by='admin' WHERE id=?",
                  (now, fb_id))
    return {"ok": True}


@router.post("/api/admin/feedback/{fb_id}/promote",
             dependencies=[Depends(require_admin)])
def admin_promote_to_fewshot(fb_id: int):
    """Promote a thumbs-UP reply to the few-shot examples library.
    Stored under config key 'chat.fewshot_examples' (JSON list).
    System-prompt builders read this and prepend up to N best examples."""
    with db.connect() as c:
        row = c.execute("""
            SELECT prompt_text, response_text FROM chat_feedback
            WHERE id=? AND rating=1
        """, (fb_id,)).fetchone()
        if not row or not row["prompt_text"] or not row["response_text"]:
            raise HTTPException(status_code=400, detail="not a promotable up-voted reply")
        # Read existing examples
        cfg_row = c.execute("SELECT value FROM config WHERE key='chat.fewshot_examples'").fetchone()
        try:
            examples = json.loads(cfg_row["value"]) if cfg_row else []
        except Exception:
            examples = []
        examples.append({
            "prompt": row["prompt_text"],
            "response": row["response_text"],
            "source_id": fb_id,
            "added_at": datetime.now(timezone.utc).isoformat(),
        })
        # Cap at 50 most recent — avoid prompt bloat
        examples = examples[-50:]
        now = datetime.now(timezone.utc).isoformat()
        c.execute("""
            INSERT INTO config (key, value, updated_at) VALUES ('chat.fewshot_examples', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (json.dumps(examples), now))
        c.execute("UPDATE chat_feedback SET promoted_to_fewshot=1 WHERE id=?", (fb_id,))
    return {"ok": True, "examples_count": len(examples)}


# ─────────────────────────────────────────────────────────────────────
# AI Critic agent — RLAIF
# ─────────────────────────────────────────────────────────────────────
def _build_critic_prompt(user_msg: str, bot_reply: str,
                         tools_called: list[str] | None) -> str:
    """Build the rubric prompt sent to the critic model."""
    rubric_lines = "\n".join(
        f"- {dim}: {desc}" for dim, desc in RUBRIC_DIMENSIONS.items()
    )
    tools_block = ""
    if tools_called:
        tools_block = f"\nTools called by the bot: {', '.join(tools_called)}"
    return f"""You are evaluating a Servia chatbot reply. Servia is a UAE home-services
platform — cleaning, plumbing, electrical, pest control, AC, etc. The bot
should be warm but direct, quote real AED prices, never invent services,
and call the right tool when the customer wants to book or get a quote.

USER ASKED:
{user_msg}
{tools_block}

BOT REPLIED:
{bot_reply}

Score the reply 0-10 on EACH of these dimensions:
{rubric_lines}

Return ONLY a JSON object on a single line, no markdown, no commentary:
{{"accurate": N, "on_brand": N, "tool_correct": N, "helpful": N, "concise": N, "notes": "ONE-SENTENCE rationale"}}
"""


async def _score_one(user_msg: str, bot_reply: str,
                     tools_called: list[str] | None,
                     critic_model: str | None = None) -> dict:
    """Run the critic on one reply. Returns scores dict or {"error": ...}."""
    from . import ai_router
    prompt = _build_critic_prompt(user_msg, bot_reply, tools_called)
    res = await ai_router.call_with_cascade(prompt, persona="critic",
                                             preferred=critic_model)
    if not res.get("ok"):
        return {"error": res.get("error", "all providers failed")}
    text = (res.get("text") or "").strip()
    # Strip code fences if model added them despite the instruction
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    # Find the first JSON object
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < 0:
            return {"error": "no JSON in critic response", "raw": text[:200]}
        parsed = json.loads(text[start:end+1])
    except Exception as e:
        return {"error": f"JSON parse: {e}", "raw": text[:200]}
    scores: dict[str, float] = {}
    for dim in RUBRIC_DIMENSIONS:
        v = parsed.get(dim, 5)
        try:
            scores[dim] = float(v)
        except Exception:
            scores[dim] = 5.0
        # Clamp
        if scores[dim] < 0: scores[dim] = 0.0
        if scores[dim] > 10: scores[dim] = 10.0
    avg = sum(scores.values()) / len(scores)
    return {
        "scores": scores,
        "avg": avg,
        "notes": (parsed.get("notes") or "")[:500],
        "critic_model": res.get("provider", "") + "/" + res.get("model", ""),
    }


async def _run_critic_batch_async(limit: int = 100, since_hours: int = 24) -> dict:
    """Score the last `limit` AI replies in the last `since_hours` hours.
    Skips messages that already have a critic_score row."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
    with db.connect() as c:
        # Get assistant messages without a prior critic score, paired with
        # the immediately-preceding user message (the prompt that triggered them).
        rows = c.execute("""
            SELECT a.id AS msg_id, a.session_id, a.content AS bot_reply,
                   a.tool_calls_json, a.created_at,
                   (SELECT u.content FROM conversations u
                    WHERE u.session_id=a.session_id AND u.role='user'
                      AND u.id < a.id
                    ORDER BY u.id DESC LIMIT 1) AS user_msg
            FROM conversations a
            WHERE a.role='assistant'
              AND a.created_at >= ?
              AND a.id NOT IN (SELECT message_id FROM critic_scores WHERE message_id IS NOT NULL)
            ORDER BY a.id DESC
            LIMIT ?
        """, (cutoff, limit)).fetchall()
        candidates = [dict(r) for r in rows]

    scored = 0
    errors = 0
    total_avg = 0.0
    flagged = 0
    now = datetime.now(timezone.utc).isoformat()
    for row in candidates:
        user_msg = (row.get("user_msg") or "")[:8000]
        bot_reply = (row.get("bot_reply") or "")[:16000]
        if not user_msg or not bot_reply:
            continue
        tools = []
        if row.get("tool_calls_json"):
            try:
                tcj = json.loads(row["tool_calls_json"])
                if isinstance(tcj, list):
                    tools = [t.get("name", "") for t in tcj if isinstance(t, dict)]
                elif isinstance(tcj, dict):
                    tools = list(tcj.keys())
            except Exception:
                pass
        result = await _score_one(user_msg, bot_reply, tools)
        if "error" in result:
            errors += 1
            continue
        avg = result["avg"]
        is_flagged = 1 if avg < 6 else 0
        with db.connect() as c:
            c.execute("""
                INSERT INTO critic_scores
                  (message_id, session_id, prompt_text, response_text,
                   model_used, scores_json, avg_score, critic_notes,
                   critic_model, flagged, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (row["msg_id"], row["session_id"], user_msg, bot_reply,
                  "", json.dumps(result["scores"]), avg, result["notes"],
                  result["critic_model"], is_flagged, now))
        scored += 1
        total_avg += avg
        if is_flagged:
            flagged += 1
    return {
        "ok": True,
        "candidates_found": len(candidates),
        "scored": scored,
        "errors": errors,
        "flagged": flagged,
        "avg_score": (round(total_avg / scored, 2) if scored else None),
    }


@router.post("/api/admin/critic/run",
             dependencies=[Depends(require_admin)])
async def admin_run_critic(limit: int = 50, since_hours: int = 24):
    """Trigger a critic-agent batch run. Admin-callable, ~30-60 sec for 50."""
    return await _run_critic_batch_async(limit=limit, since_hours=since_hours)
