from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, List, Optional, Union, Literal

from pydantic import BaseModel, Field, ConfigDict


class Mode(str, Enum):
    assist = "assist"
    draft = "draft"
    autopilot = "autopilot"


class RiskColor(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


class ErrorCode(str, Enum):
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class SourceType(str, Enum):
    kb = "kb"
    rag = "rag"
    manual = "manual"
    web = "web"
    none = "none"


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    version: str
    ref: str
    source_type: SourceType = SourceType.kb
    relevance: float = Field(ge=0.0, le=1.0)


class Meta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    timestamp: datetime
    latency_ms: int = Field(ge=0)
    lead_id: Optional[str] = None
    user_id: Optional[str] = None

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)


class ErrorBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ErrorCode
    user_message: str
    debug_message: str
    retryable: bool


class EnvelopeBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    client_message: str
    manager_note: str = ""
    mode: Mode
    confidence: float = Field(ge=0.0, le=1.0)

    risk_color: RiskColor
    risk_reason: str

    requires_review: bool
    requires_review_reason: str = ""

    sources: List[Source] = Field(default_factory=list)
    policy_id: str
    data: Any | None = None

    meta: Meta


class EnvelopeSuccess(EnvelopeBase):
    ok: Literal[True] = True


class EnvelopeError(EnvelopeBase):
    ok: Literal[False] = False
    error: ErrorBlock
    risk_color: Literal[RiskColor.red] = RiskColor.red
    requires_review: Literal[True] = True
    policy_id: Literal["ERROR_SAFE_01"] = "ERROR_SAFE_01"


# Root union for FastAPI response_model usage if needed
EnvelopeRoot = Annotated[Union[EnvelopeSuccess, EnvelopeError], Field(discriminator="ok")]
