from fastapi import FastAPI, Request
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


from app.db import Base, engine
from app.api.v1.router import router as api_v1_router
from app.api.v1.schemas import ErrorResponse

app = FastAPI(title="TravelAI Backend")

#Base.metadata.create_all(bind=engine)

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
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="validation_error",
            details=str(exc),
        ).dict(),
    )

# API v1
app.include_router(api_v1_router)

# Healthcheck (no versioning)
@app.get("/health")
def health():
    ai_enabled = bool(os.getenv("OPENAI_API_KEY"))
    vector_enabled = bool(os.getenv("QDRANT_URL") or os.getenv("PGVECTOR_DSN"))
    return {"status": "ok", "ai_enabled": ai_enabled, "vector_enabled": vector_enabled}
