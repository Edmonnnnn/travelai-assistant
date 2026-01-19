from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    risk_color: str
    risk_reason: str
    requires_review: bool
    requires_review_reason: str


_HIGH_RISK_KEYWORDS = (
    # RU
    "виза",
    "шенген",
    "штраф",
    "оплата",
    "платеж",
    "санкции",
    "багаж",
    # EN
    "visa",
    "schengen",
    "fine",
    "penalty",
    "payment",
    "charge",
    "refund",
    "sanction",
    "baggage",
    "luggage",
)


def _normalize_text(text: str) -> str:
    normalized = (text or "").lower().strip()
    return " ".join(normalized.split())


def assess_risk(text: str, sources_count: int) -> RiskDecision:
    normalized = _normalize_text(text)
    has_high_risk = any(keyword in normalized for keyword in _HIGH_RISK_KEYWORDS)
    if has_high_risk and sources_count == 0:
        return RiskDecision(
            risk_color="red",
            risk_reason="High-risk topic without sources",
            requires_review=True,
            requires_review_reason="No sources for high-risk topic",
        )
    return RiskDecision(
        risk_color="green",
        risk_reason="No high-risk indicators",
        requires_review=False,
        requires_review_reason="",
    )
