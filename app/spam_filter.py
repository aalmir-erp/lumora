"""Deterministic spam / off-topic pre-filter for inbound chat + WhatsApp.

Founder reported the bot was burning LLM tokens replying politely to
spam messages (Amazon review scams, electronics resale ads, room rental
listings, Arabic relationship spam, etc.). At AED 0.02 per spam reply
this adds up fast.

This module runs BEFORE the LLM. If a message matches a spam pattern, we
return a one-line canned reply (cost: $0) and never call Claude. The
canned reply is short, professional, and ANTI-engaging — it does not
ask "is there anything else I can help with?" because doing so invites
another spammy reply.

Public surface:
    classify(text: str) -> {"category": str | None, "confidence": float,
                            "reply_en": str, "reply_ar": str}

    is_spam(text: str) -> bool   (convenience: True if category is not None)

Categories caught:
    - amazon_review_scam     "review for refund" / "PayPal fee covered"
    - electronics_resale     RAM/SSD/processor specs being sold
    - property_rental        room/bedspace/studio for rent
    - crypto_investment      BTC/USDT/forex/earn-from-home
    - arabic_relationship    Arabic relationship/dating spam
    - off_topic_too_short    < 3 meaningful words, no service keyword
"""
from __future__ import annotations

import re
from typing import Any

# --------------------------------------------------------------------------
# Category patterns. Each is a list of regex/keyword sets — message must hit
# at least N of them (per the THRESHOLDS dict) to be classified as spam.
# Keeping the patterns DELIBERATELY simple so false-positives stay low.
# --------------------------------------------------------------------------

_AMAZON_REVIEW_PATTERNS = [
    r"\bAMAZON\b.{0,50}\b(REVIEW|REFUND|FEE COVERED)\b",
    r"\bPRODUCT\s+REVIEW\s+REQUIRED\b",
    r"\bPAYPAL\s+FEE\s+COVERED\b",
    r"\bCOMPLETE\s+REFUND\b",
    r"\b(buy|purchase)\s+(my|our)\s+product.{0,30}review",
    r"\bUSDT\s+(payment|paid|refund)\b",
]

_ELECTRONICS_RESALE_PATTERNS = [
    r"\b(Intel|AMD|Apple)\s+(Core|Ryzen|M[1-4])\b",
    r"\bRTX\s*\d{3,4}\b",
    r"\b(GeForce|Radeon)\b",
    r"\b\d+\s*GB\b.{0,40}\b(RAM|DDR\d|SSD|NVMe|GDDR\d)\b",
    r"\b\d+\s*(TB|GB)\s+(SSD|NVMe|HDD)\b",
    r"\bReady\s+Stock\b",
    r"\b(Brand\s+New|Sealed|Original)\s+(Box|Pack|piece|set)\b",
    r"\b\d{4}\s*x\s*\d{4}\b.{0,20}\b(IPS|OLED|Display|monitor)\b",
    # Generic spec dump: multiple ALL-CAPS spec lines with measurements
    r"^\*[A-Z0-9]{4,}\*$",  # "*83EY000XUS*" pattern
]

_PROPERTY_RENTAL_PATTERNS = [
    r"\b(room|bedspace|bed\s+space|studio|partition)\s+(available|for\s+rent|rental)\b",
    r"\b(monthly|per\s+month)\s+(rent|rental)\b",
    r"\bAED\s+\d+\s*(/|per)\s+month\b",
    r"\bavailable\s+in\s+(maza|jvc|marina|sharjah|bur\s+dubai|jbr)\b",
    r"\bsharing\s+(room|accommodation|bedspace)\b",
    r"\b(single|double|family)\s+room\b.{0,30}\b(available|rent|month)\b",
    r"\b\d+\s*BHK\b.{0,30}\bfor\s+rent\b",
]

_CRYPTO_INVESTMENT_PATTERNS = [
    r"\b(BTC|USDT|ETH|crypto|bitcoin|forex)\b.{0,60}\b(invest|profit|earn|trading|opportunity|ROI)\b",
    r"\bearn\s+\$?\d{2,5}\s+(daily|per\s+day|a\s+day|weekly|monthly)\b",
    r"\binvestment\s+opportunity\b",
    r"\bguaranteed\s+(returns?|profits?)\b",
    r"\b\d{2,3}%\s+(weekly|monthly|guaranteed|profit|return)\b",
    r"\b(MLM|pyramid|binary)\s+(plan|scheme|network)\b",
]

# Arabic relationship / dating / off-topic patterns. Keep tight to avoid
# false-positives on Arabic service inquiries.
_ARABIC_RELATIONSHIP_PATTERNS = [
    r"ابعد عن[هها]\s+نصيحه",  # "stay away from him/her, advice"
    r"\bحب\b.{0,20}\b(زواج|قلب|عشق)\b",
    r"رقم.*بنت|بنت.*رقم",  # "girl's number" patterns
]

# Generic short / no-keyword detector. Used as a last resort.
_SERVICE_KEYWORDS = {
    # English
    "clean", "cleaning", "maid", "ac", "aircon", "ac service", "plumb",
    "electric", "handyman", "pest", "paint", "move", "sofa", "carpet",
    "service", "book", "quote", "price", "cost", "fix", "repair",
    "deep clean", "tow", "recovery", "battery", "tyre", "tire", "chauffeur",
    "driver", "airport", "delivery",
    # Arabic
    "تنظيف", "صيانة", "مكيف", "خادمة", "سباك", "كهربائي", "حشرات",
    "نقل", "اثاث", "حجز", "سعر", "خدمة",
}


# Confidence thresholds per category (out of total patterns in that category)
_THRESHOLDS = {
    "amazon_review_scam":   1,  # 1 strong hit = block (these are very distinctive)
    "electronics_resale":   2,  # need 2 hits to avoid false-positive on legitimate AC unit specs
    "property_rental":      1,
    "crypto_investment":    1,
    "arabic_relationship":  1,
    "off_topic_too_short":  1,
}


# Canned replies (EN + AR). Short, polite, NOT inviting further reply.
_REPLIES = {
    "amazon_review_scam": {
        "en": ("Hi 👋 This is **Servia**, a UAE home services platform — "
               "we don't do product reviews, refunds, or PayPal transactions. "
               "You've reached the wrong number."),
        "ar": ("مرحباً 👋 هذه **سيرفيا**، منصة خدمات منزلية في الإمارات — "
               "لا نقوم بمراجعات المنتجات أو الاسترجاع. لقد وصلت لرقم خاطئ."),
    },
    "electronics_resale": {
        "en": ("Hi 👋 This is **Servia**, a UAE home services platform "
               "(cleaning, AC, plumbing, etc.) — we don't buy or sell "
               "electronics. Try Dubizzle or Facebook Marketplace."),
        "ar": ("مرحباً 👋 هذه **سيرفيا**، منصة خدمات منزلية في الإمارات — "
               "لا نشتري أو نبيع إلكترونيات. جرّب دوبيزل أو فيسبوك ماركت بليس."),
    },
    "property_rental": {
        "en": ("Hi 👋 **Servia** is a UAE home services platform "
               "(cleaning, AC, repairs) — we don't list rooms or property. "
               "Try Dubizzle, Bayut, or Property Finder."),
        "ar": ("مرحباً 👋 **سيرفيا** هي منصة خدمات منزلية في الإمارات — "
               "لا نقوم بتأجير الغرف أو العقارات. جرّب دوبيزل أو بيوت."),
    },
    "crypto_investment": {
        "en": ("Hi 👋 **Servia** is a UAE home services platform. "
               "We don't offer investments or financial services."),
        "ar": ("مرحباً 👋 **سيرفيا** منصة خدمات منزلية. لا نقدم استثمارات "
               "أو خدمات مالية."),
    },
    "arabic_relationship": {
        "en": ("Hi 👋 **Servia** is a UAE home services platform "
               "(cleaning, AC, repairs)."),
        "ar": ("مرحباً 👋 **سيرفيا** منصة خدمات منزلية في الإمارات "
               "(تنظيف، تكييف، صيانة). ربما وصلت لرقم خاطئ."),
    },
    "off_topic_too_short": {
        "en": ("Hi 👋 I'm **Servia**, UAE home services. Tell me which "
               "service you need (cleaning, AC, plumber, handyman, etc.) "
               "and I'll quote it instantly."),
        "ar": ("مرحباً 👋 أنا **سيرفيا**، خدمات منزلية في الإمارات. "
               "أخبرني بالخدمة المطلوبة (تنظيف، تكييف، سباك، إلخ)."),
    },
}


def _count_matches(text: str, patterns: list[str], ignore_case: bool = True) -> int:
    flags = re.IGNORECASE if ignore_case else 0
    return sum(1 for p in patterns if re.search(p, text, flags))


def _looks_arabic(text: str) -> bool:
    """Returns True if more than 30% of characters are Arabic."""
    if not text: return False
    arabic = sum(1 for ch in text if "؀" <= ch <= "ۿ")
    letters = sum(1 for ch in text if ch.isalpha())
    return letters > 0 and (arabic / max(letters, 1)) > 0.3


def _is_off_topic_short(text: str) -> bool:
    """True if message is <= 3 words AND no service keyword."""
    if not text: return False
    words = [w for w in re.findall(r"\b[\w']+\b", text.lower()) if len(w) > 1]
    if len(words) > 3:
        return False
    low = text.lower()
    for kw in _SERVICE_KEYWORDS:
        if kw in low:
            return False
    return True


def classify(text: str) -> dict[str, Any]:
    """Return classification result. category=None means NOT spam."""
    if not text or not isinstance(text, str):
        return {"category": None, "confidence": 0.0, "reply_en": "", "reply_ar": ""}

    t = text.strip()
    is_arabic = _looks_arabic(t)

    # Run each detector and pick the highest-confidence match.
    candidates: list[tuple[str, int]] = []

    n = _count_matches(t, _AMAZON_REVIEW_PATTERNS)
    if n >= _THRESHOLDS["amazon_review_scam"]:
        candidates.append(("amazon_review_scam", n))

    n = _count_matches(t, _ELECTRONICS_RESALE_PATTERNS)
    if n >= _THRESHOLDS["electronics_resale"]:
        candidates.append(("electronics_resale", n))

    n = _count_matches(t, _PROPERTY_RENTAL_PATTERNS)
    if n >= _THRESHOLDS["property_rental"]:
        candidates.append(("property_rental", n))

    n = _count_matches(t, _CRYPTO_INVESTMENT_PATTERNS)
    if n >= _THRESHOLDS["crypto_investment"]:
        candidates.append(("crypto_investment", n))

    if is_arabic:
        n = _count_matches(t, _ARABIC_RELATIONSHIP_PATTERNS)
        if n >= _THRESHOLDS["arabic_relationship"]:
            candidates.append(("arabic_relationship", n))

    # v1.24.228 — off_topic_too_short DISABLED as an auto-block path.
    # The previous version caught legitimate short first messages
    # ("hi", "how much", "what time", etc.) and replied with the canned
    # "tell me which service" message — but the LLM bot is designed
    # to handle exactly those greetings properly with an intake prompt
    # + price calculator. Blocking them at the spam layer prevented
    # the bot from doing its actual job. Verified by test_e2e_chat,
    # test_quote_card_e2e, test_address_card_e2e all failing with the
    # canned reply appearing where bot output was expected.
    # Keeping the detector function around for future telemetry but
    # NOT firing it as a category.

    if not candidates:
        return {"category": None, "confidence": 0.0, "reply_en": "", "reply_ar": ""}

    # Highest match count wins
    candidates.sort(key=lambda x: -x[1])
    cat, hits = candidates[0]
    confidence = min(1.0, hits / 3.0)

    replies = _REPLIES.get(cat, _REPLIES["off_topic_too_short"])
    return {
        "category": cat,
        "confidence": round(confidence, 2),
        "reply_en": replies["en"],
        "reply_ar": replies["ar"],
        "is_arabic": is_arabic,
    }


def is_spam(text: str) -> bool:
    """Convenience: True if classify(text) returns a non-None category."""
    return classify(text)["category"] is not None


def reply_for(text: str) -> str | None:
    """Return the appropriate canned reply (Arabic or English) for the
    message, or None if it's not spam. Picks Arabic reply when the input
    looks Arabic, English otherwise."""
    c = classify(text)
    if not c["category"]:
        return None
    return c["reply_ar"] if c.get("is_arabic") else c["reply_en"]
