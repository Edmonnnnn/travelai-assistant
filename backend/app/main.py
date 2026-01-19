from fastapi import FastAPI, Request
import os
from json import JSONDecodeError
from time import perf_counter

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.middleware.request_id import RequestIdMiddleware
from app.core.middleware.access_log import AccessLogMiddleware
from app.core.envelope.builder import error_envelope
from app.core.envelope.schema import ErrorCode

from app.api.health import router as health_router
from app.api.router import router as api_router

from app.db import Base, engine
from app.api.v1.router import router as api_v1_router


class Utf8JsonMiddleware(BaseHTTPMiddleware):
    """
    Ensures JSON responses always include charset=utf-8.
    Fixes Windows/PowerShell clients showing mojibake for Cyrillic.
    """
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        ct = resp.headers.get("content-type", "")
        # Only adjust JSON responses that forgot to declare charset.
        if ct.startswith("application/json") and "charset=" not in ct:
            resp.headers["content-type"] = "application/json; charset=utf-8"
        return resp


app = FastAPI(title="TravelAI Backend")

# Request ID must be early (so all logs/handlers can reuse it)
app.add_middleware(RequestIdMiddleware)

# Access log after request-id (so it can log request_id)
app.add_middleware(AccessLogMiddleware)

# Force utf-8 JSON header for all json responses
app.add_middleware(Utf8JsonMiddleware)

# Routers (no versioning)
app.include_router(health_router)
app.include_router(api_router)

# Base.metadata.create_all(bind=engine)

# CORS — подготовка под frontend (Direct API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    start = perf_counter()
    rid = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or "rid-unknown"
    fields = []
    for err in exc.errors():
        loc = err.get("loc")
        if not loc:
            continue
        if isinstance(loc, (list, tuple)):
            fields.append(".".join(str(part) for part in loc))
        else:
            fields.append(str(loc))
    fields_info = ", ".join(sorted(set(fields))) if fields else "unknown"
    debug_message = f"RequestValidationError: fields={fields_info}"
    envelope = error_envelope(
        client_message="Похоже, сейчас есть техническая проблема. Попробуйте ещё раз.",
        request_id=rid,
        latency_ms=int((perf_counter() - start) * 1000),
        error_code=ErrorCode.VALIDATION_ERROR,
        retryable=True,
        user_message="без деталей",
        debug_message=debug_message,
        manager_note="Validation error in request",
    )
    return JSONResponse(
        status_code=422,
        content=envelope.model_dump(mode="json"),
    )


@app.exception_handler(JSONDecodeError)
async def json_decode_exception_handler(request: Request, exc: JSONDecodeError):
    start = perf_counter()
    rid = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or "rid-unknown"
    debug_message = f"JSONDecodeError: {exc.msg}"
    envelope = error_envelope(
        client_message="Похоже, сейчас есть техническая проблема. Попробуйте ещё раз.",
        request_id=rid,
        latency_ms=int((perf_counter() - start) * 1000),
        error_code=ErrorCode.VALIDATION_ERROR,
        retryable=True,
        user_message="без деталей",
        debug_message=debug_message,
        manager_note="JSON decode error",
    )
    return JSONResponse(
        status_code=400,
        content=envelope.model_dump(mode="json"),
    )

# API v1
app.include_router(api_v1_router)
