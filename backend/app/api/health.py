from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import text

from app.core.envelope.builder import error_envelope, success_envelope
from app.core.envelope.schema import ErrorCode
from app.db import SessionLocal

router = APIRouter()


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        return header_id
    return f"rid-{uuid4().hex[:8]}"


@router.get("/health")
def health_check(request: Request, response: Response):
    start = perf_counter()
    request_id = _get_request_id(request)

    try:
        if SessionLocal is None or not callable(SessionLocal):
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            latency_ms = int((perf_counter() - start) * 1000)
            return success_envelope(
                client_message="degraded",
                request_id=request_id,
                latency_ms=latency_ms,
                sources=[],
            )

        overall_status = "degraded"
        db = None

        try:
            db = SessionLocal()
            db.execute(text("SELECT 1")).scalar()
            overall_status = "ok"
        except Exception:
            overall_status = "degraded"
        finally:
            if db is not None:
                db.close()

        latency_ms = int((perf_counter() - start) * 1000)
        return success_envelope(
            client_message=overall_status,
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
