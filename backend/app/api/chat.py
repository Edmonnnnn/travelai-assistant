# backend/app/api/chat.py
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.envelope.builder import error_envelope, success_envelope
from app.core.envelope.schema import ErrorCode, Mode
from app.core.policy.risk import assess_risk
import logging

router = APIRouter(tags=["chat"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    lead_id: str | None = None
    user_id: str | None = None
    mode: str | None = None  # assist|draft|autopilot


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        return header_id
    return f"rid-{uuid4().hex[:8]}"


def _get_mode(value: str | None) -> Mode:
    if not value:
        return Mode.assist
    try:
        return Mode(value)
    except ValueError:
        return Mode.assist


@router.post("/chat")
def chat(payload: ChatIn, request: Request):
    start = perf_counter()
    request_id = _get_request_id(request)
    sources: list = []
    logging.getLogger("uvicorn.error").info("payload.message=%r", payload.message)
    decision = assess_risk(payload.message, len(sources))

    try:
        latency_ms = int((perf_counter() - start) * 1000)
        return success_envelope(
            client_message="stub",
            request_id=request_id,
            latency_ms=latency_ms,
            sources=sources,
            mode=_get_mode(payload.mode),
            risk_color=decision.risk_color,
            risk_reason=decision.risk_reason,
            requires_review=decision.requires_review,
            requires_review_reason=decision.requires_review_reason,
            lead_id=payload.lead_id,
            user_id=payload.user_id,
        )
    except Exception as e:
        latency_ms = int((perf_counter() - start) * 1000)
        return error_envelope(
            client_message="error",
            request_id=request_id,
            latency_ms=latency_ms,
            error_code=ErrorCode.INTERNAL_ERROR,
            debug_message=str(e),
            sources=sources,
            mode=_get_mode(payload.mode),
            lead_id=payload.lead_id,
            user_id=payload.user_id,
        )
