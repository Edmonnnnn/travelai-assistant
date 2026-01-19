from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .schema import RiskColor


# High-risk topics per A2 scope: visas/fines/payments/sanctions/baggage.
# Keep it simple and deterministic (no AI).
_HIGH_RISK_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bvisa\b", re.IGNORECASE),
    re.compile(r"\bшенген\b", re.IGNORECASE),
    re.compile(r"\bвиза\b", re.IGNORECASE),
    re.compile(r"\bштраф\b", re.IGNORECASE),
    re.compile(r"\bоплат(а|ы|ить|ил)\b", re.IGNORECASE),
    re.compile(r"\bплат(еж|ежи|ить)\b", re.IGNORECASE),
    re.compile(r"\bsanction(s)?\b", re.IGNORECASE),
    re.compile(r"\bсанкц", re.IGNORECASE),
    re.compile(r"\bбагаж\b", re.IGNORECASE),
    re.compile(r"\bbaggage\b", re.IGNORECASE),
]


def is_high_risk_query(text: str) -> bool:
    """Return True if the text matches any high-risk topic pattern."""
    if not text:
        return False
    t = text.strip()
    if not t:
        return False
    return any(p.search(t) for p in _HIGH_RISK_PATTERNS)


def evaluate_policy(
    *,
    user_text: str,
    sources_count: int,
) -> Tuple[RiskColor, bool, str, str]:
    """
    Policy decision for risk and HITL review.

    Returns:
      (risk_color, requires_review, risk_reason, requires_review_reason)

    Rules (A2):
    - Never fabricate sources. If KB/RAG yields nothing => sources=[]
    - High-risk topic + no sources => red + requires_review=true
    - Non-high-risk + no sources => yellow (general guidance allowed) + review=false by default
    - Any topic + sources present => green by default (still can be yellow later if needed)
    """
    has_sources = sources_count > 0
    high_risk = is_high_risk_query(user_text)

    if high_risk and not has_sources:
        return (
            "red",
            True,
            "высокий риск: нужна проверка по источникам",
            "нет источников по high-risk теме — требуется менеджер",
        )

    if not has_sources:
        return (
            "yellow",
            False,
            "нет подтверждённых источников — нужны уточнения",
            "",
        )

    return (
        "green",
        False,
        "есть подтверждённые источники",
        "",
    )
