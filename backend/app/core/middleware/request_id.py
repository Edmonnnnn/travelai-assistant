from __future__ import annotations

import uuid
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_HEADER = "X-Request-ID"


def _new_request_id() -> str:
    # Short but unique enough for logs; keep it URL/header safe.
    return uuid.uuid4().hex


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Ensures every request has a request_id:
    - accepts incoming X-Request-ID
    - otherwise generates one
    - stores at request.state.request_id
    - echoes X-Request-ID on response
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get(_HEADER)
        if not rid or not rid.strip():
            rid = _new_request_id()
        rid = rid.strip()

        request.state.request_id = rid

        response = await call_next(request)
        response.headers[_HEADER] = rid
        return response
