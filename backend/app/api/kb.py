# backend/app/api/kb.py
from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Query, Request

from app.core.envelope.builder import error_envelope, success_envelope
from app.core.envelope.schema import ErrorCode

router = APIRouter(tags=["kb"])


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        return header_id
    return f"rid-{uuid4().hex[:8]}"


@router.get("/kb")
def kb(request: Request, q: str | None = Query(default=None, max_length=200)):
    start = perf_counter()
    request_id = _get_request_id(request)

    try:
        latency_ms = int((perf_counter() - start) * 1000)
        return success_envelope(
            client_message="stub",
            request_id=request_id,
            latency_ms=latency_ms,
            sources=[],
        )
    except Exception as e:
        latency_ms = int((perf_counter() - start) * 1000)
        return error_envelope(
            client_message="error",
            request_id=request_id,
            latency_ms=latency_ms,
            error_code=ErrorCode.INTERNAL_ERROR,
            debug_message=str(e),
            sources=[],
        )
