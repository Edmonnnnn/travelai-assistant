from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from .schema import (
    EnvelopeSuccess,
    EnvelopeError,
    ErrorBlock,
    Meta,
    Mode,
    RiskColor,
    ErrorCode,
    Source,
)


def _now_utc_dt() -> datetime:
    return datetime.now(timezone.utc)


def build_meta(
    *,
    request_id: str,
    latency_ms: int,
    lead_id: Optional[str] = None,
    user_id: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> Meta:
    return Meta(
        request_id=request_id,
        timestamp=timestamp or _now_utc_dt(),
        latency_ms=latency_ms,
        lead_id=lead_id,
        user_id=user_id,
    )


def success_envelope(
    *,
    client_message: str,
    request_id: str,
    latency_ms: int,
    mode: Mode = Mode.assist,
    confidence: float = 0.0,
    risk_color: RiskColor = RiskColor.green,
    risk_reason: str = "",
    requires_review: bool = False,
    requires_review_reason: str = "",
    sources: Optional[List[Source]] = None,
    policy_id: str = "RAG_SAFE_01",
    manager_note: str = "",
    lead_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> EnvelopeSuccess:
    meta = build_meta(
        request_id=request_id,
        latency_ms=latency_ms,
        lead_id=lead_id,
        user_id=user_id,
    )
    return EnvelopeSuccess(
        ok=True,
        client_message=client_message,
        manager_note=manager_note,
        mode=mode,
        confidence=confidence,
        risk_color=risk_color,
        risk_reason=risk_reason,
        requires_review=requires_review,
        requires_review_reason=requires_review_reason,
        sources=sources or [],
        policy_id=policy_id,
        meta=meta,
    )


def error_envelope(
    *,
    client_message: str,
    request_id: str,
    latency_ms: int,
    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
    retryable: bool = True,
    user_message: str = "без деталей",
    debug_message: str = "",
    mode: Mode = Mode.assist,
    confidence: float = 0.0,
    risk_reason: str = "техническая ошибка",
    requires_review_reason: str = "нужно проверить инцидент",
    manager_note: str = "Кратко: что упало и где искать.",
    sources: Optional[List[Source]] = None,
    lead_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> EnvelopeError:
    meta = build_meta(
        request_id=request_id,
        latency_ms=latency_ms,
        lead_id=lead_id,
        user_id=user_id,
    )
    err = ErrorBlock(
        code=error_code,
        user_message=user_message,
        debug_message=debug_message,
        retryable=retryable,
    )

    return EnvelopeError(
        ok=False,
        client_message=client_message,
        manager_note=manager_note,
        mode=mode,
        confidence=confidence,
        risk_color=RiskColor.red,
        risk_reason=risk_reason,
        requires_review=True,
        requires_review_reason=requires_review_reason,
        sources=sources or [],
        policy_id="ERROR_SAFE_01",
        meta=meta,
        error=err,
    )
