"""v1.24.113 — Defamation-safe content filter for autoblog.

Founder reported a live article on /blog/sharjah-aljada-... that said:

  > "Aljada towers built between 2021-2024 have a bathroom-humidity
  >  design issue."

That's an unsubstantiated factual claim about a real Arada master-plan.
Exposes Servia to defamation claims under UAE Penal Code Article 372
(harming the reputation of an identifiable entity).

This module scans LLM-generated text BEFORE it's persisted. If the text
hits any defamation pattern, the autoblog tick rejects the result and
either retries with a fresh generation OR records the failure in
last_run.err so the admin sees WHY no post was published.

Two-stage detection:

1. HARD blockers — phrases that are defamatory or risky on their own.
   These reject immediately:
     - "towers built between" / "built in YYYY" near a project name
     - "design issue", "design flaw", "construction defect" near any
       named place
     - "infestation problem in" + a named area
     - Comparative negatives ("X is worse than Y")

2. SOFT flags — patterns that need human review. Logged but allowed.

The list is conservative: it errs toward false-positives. Better to
re-generate a clean article than ship a defamatory one.
"""
from __future__ import annotations

import re
from typing import NamedTuple


# Specific developer / project names that should NEVER appear near
# negative phrasing. These are the entities most likely to sue.
DEVELOPER_NAMES = (
    # Major developers
    "arada", "emaar", "damac", "nakheel", "sobha", "aldar",
    "meraas", "dubai properties", "wasl", "al habtoor",
    "ellington", "azizi", "mag ", "tiger", "deyaar",
    "union properties", "dubai holding", "binghatti", "danube",
    # Specific master-plan / branded community names (case-insensitive)
    "aljada", "al jada",
    "damac hills", "akoya", "akoya oxygen",
    "arabian ranches",
    "tilal city",
    "mudon",
    "jumeirah park", "jumeirah islands",
    "town square",
    "city walk",
    "bluewaters",
    "madinat jumeirah", "mira",
    "mirdif hills",
    "saadiyat beach", "saadiyat island",
    "yas acres", "yas island",
    "reem hills", "al reem",
    "ghantoot",
    "al zahia",
    "azha",
    "khalifa city", "mohamed bin zayed",
    "international city",
    # Individual tower names (a tiny sample — keep extending)
    "burj khalifa", "burj al arab", "ain dubai",
    "address tower", "address residences",
)


# Negative descriptors that, when paired with a developer/project name
# within proximity, become defamatory.
NEGATIVE_NEAR_PROJECT = (
    "design issue", "design flaw", "design defect",
    "construction problem", "construction issue", "construction defect",
    "structural issue", "structural fault", "structural problem",
    "infestation problem", "infestation issue",
    "humidity issue", "humidity problem", "damp problem", "damp issue",
    "leak issue", "leak problem",
    "plumbing fault", "plumbing problem", "plumbing defect",
    "electrical fault", "electrical defect",
    "ac fault", "a/c fault", "air-con fault",
    "ventilation problem", "ventilation defect", "ventilation issue",
    "design fault",
    "built poorly", "poorly built", "badly built",
    "design failure", "engineering failure",
    "quality issue", "quality problem",
    "cracked", "cracking", "subsidence",
    "mold problem", "mould problem", "mold issue", "mould issue",
)


# Date-range claims tied to construction. The original Aljada article
# said "towers built between 2021-2024 have a humidity issue". Any
# phrasing like that is unsubstantiated and risky.
DATE_CLAIM_PATTERNS = (
    r"\btowers?\s+built\s+(?:between|in|during)\b",
    r"\bbuilt\s+between\s+\d{4}\s*[-to]+\s*\d{4}\b",
    r"\b(?:tower|building|compound)s?\s+(?:from|completed in)\s+\d{4}\s+(?:have|has|suffer|exhibit)\b",
)


# Comparative defamation: "X has more pests than Y", "X is worse than Y",
# etc. Anything that ranks a real neighborhood negatively against
# another. These patterns are applied to the ORIGINAL-case text (not
# lowercased) so the [A-Z][a-zA-Z]+ proper-noun gate actually works.
# v1.24.120 bug fix: previously the engine lowercased AND set IGNORECASE,
# which defeated the capital-letter check and flagged generic phrases
# like "more cockroaches than before" as defamation. Now these patterns
# run case-sensitively against original text via _find_pattern_cased().
COMPARATIVE_PATTERNS = (
    r"\b(?:more|worse|poorer|fewer|less)\s+\w+\s+than\s+(?:[A-Z][a-zA-Z]+\s+){0,2}[A-Z][a-zA-Z]+\b",
    r"\b(?:Unlike|Compared to)\s+[A-Z][a-zA-Z]+,?\s+[A-Z][a-zA-Z]+\s+(?:has|suffers|struggles)\b",
)


# Specific competitor business names. Not exhaustive — extend as needed.
COMPETITOR_NAMES = (
    "homely", "matic services", "justlife", "service market",
    "urban services uae", "helpling", "tadbeer", "lugmeti",
    "sharaf dg", "carrefour services", "lulu services",
)


class Finding(NamedTuple):
    rule: str
    snippet: str
    span: tuple[int, int]


def _find_pattern(text: str, patterns: tuple[str, ...]) -> list[Finding]:
    """Find regex patterns in text. Returns Finding tuples with context."""
    out: list[Finding] = []
    lower = text.lower()
    for pat in patterns:
        for m in re.finditer(pat, lower, flags=re.IGNORECASE):
            start, end = m.span()
            # Pull 80 chars of context on each side
            ctx_start = max(0, start - 80)
            ctx_end = min(len(text), end + 80)
            out.append(Finding(rule=pat, snippet=text[ctx_start:ctx_end],
                                span=(start, end)))
    return out


def _find_pattern_cased(text: str, patterns: tuple[str, ...]) -> list[Finding]:
    """Like _find_pattern but case-SENSITIVE on the original text. Used
    for proper-noun-gated patterns (comparative defamation) where the
    [A-Z][a-zA-Z]+ gate is the whole point — lowercasing would defeat it.
    """
    out: list[Finding] = []
    for pat in patterns:
        for m in re.finditer(pat, text):  # no flags → case-sensitive
            start, end = m.span()
            ctx_start = max(0, start - 80)
            ctx_end = min(len(text), end + 80)
            out.append(Finding(rule=pat, snippet=text[ctx_start:ctx_end],
                                span=(start, end)))
    return out


def _find_negative_near_project(text: str, window: int = 200) -> list[Finding]:
    """Return Findings where a developer/project name appears within
    `window` characters of a negative descriptor. This is the main
    defamation signal."""
    out: list[Finding] = []
    lower = text.lower()
    # Pre-find every project-name span
    project_spans: list[tuple[int, int, str]] = []
    for name in DEVELOPER_NAMES:
        for m in re.finditer(r"\b" + re.escape(name) + r"\b", lower):
            project_spans.append((m.start(), m.end(), name))
    if not project_spans:
        return out
    for neg in NEGATIVE_NEAR_PROJECT:
        for m in re.finditer(r"\b" + re.escape(neg) + r"\b", lower):
            ns, ne = m.span()
            # Find a project span within `window` chars in either direction
            for ps, pe, pname in project_spans:
                if abs(ns - ps) <= window or abs(ne - pe) <= window:
                    ctx_start = max(0, min(ns, ps) - 60)
                    ctx_end = min(len(text), max(ne, pe) + 60)
                    out.append(Finding(
                        rule=f"defamation: '{neg}' within {window} chars of '{pname}'",
                        snippet=text[ctx_start:ctx_end],
                        span=(min(ns, ps), max(ne, pe)),
                    ))
                    break
    return out


def _find_competitor_names(text: str) -> list[Finding]:
    out: list[Finding] = []
    lower = text.lower()
    for name in COMPETITOR_NAMES:
        for m in re.finditer(r"\b" + re.escape(name) + r"\b", lower):
            ctx_start = max(0, m.start() - 60)
            ctx_end = min(len(text), m.end() + 60)
            out.append(Finding(
                rule=f"competitor named: '{name}'",
                snippet=text[ctx_start:ctx_end],
                span=m.span(),
            ))
    return out


def review(text: str) -> dict:
    """Scan generated text for defamation / safety issues.

    Returns a dict:
      {
        "ok": bool,                        # True if safe to publish
        "findings": list[Finding],         # what triggered the block
        "summary": str,                    # one-line reason
      }

    Caller's contract: if ok is False, REGENERATE or LOG + DROP.
    Never publish text with ok=False without explicit admin override.
    """
    findings: list[Finding] = []
    findings.extend(_find_negative_near_project(text))
    findings.extend(_find_pattern(text, DATE_CLAIM_PATTERNS))
    # Comparative patterns need ORIGINAL case so the proper-noun gate works
    findings.extend(_find_pattern_cased(text, COMPARATIVE_PATTERNS))
    findings.extend(_find_competitor_names(text))

    if findings:
        rules = ", ".join({f.rule.split(":")[0].strip() for f in findings[:5]})
        summary = (f"BLOCKED — {len(findings)} defamation/safety issue(s). "
                   f"Triggered rules: {rules[:140]}")
        return {"ok": False, "findings": findings, "summary": summary}
    return {"ok": True, "findings": [], "summary": "clean"}


def explain(findings: list[Finding]) -> str:
    """Format findings as a multi-line human-readable report.
    Used in admin UI + last_run.err."""
    if not findings:
        return "(no issues found)"
    lines = []
    for i, f in enumerate(findings[:10], 1):
        clean = f.snippet.replace("\n", " ").strip()
        if len(clean) > 180: clean = clean[:177] + "…"
        lines.append(f"  {i}. {f.rule}\n     “…{clean}…”")
    if len(findings) > 10:
        lines.append(f"  … and {len(findings) - 10} more")
    return "\n".join(lines)
