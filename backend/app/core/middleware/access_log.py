from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging.json_logger import log_event


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Logs one JSON line per request with request_id and latency.
    Risk fields are taken from request.state if set by endpoints/orchestrator.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)

            request_id = getattr(request.state, "request_id", None)
            risk_color = getattr(request.state, "risk_color", None)
            requires_review = getattr(request.state, "requires_review", None)

            log_event(
                "info",
                "http_request",
                method=request.method,
                path=request.url.path,
                status=getattr(response, "status_code", 0) if "response" in locals() else 500,
                latency_ms=latency_ms,
                request_id=request_id,
                risk_color=risk_color,
                requires_review=requires_review,
            )
