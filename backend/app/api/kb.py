# backend/app/api/kb.py
from __future__ import annotations

from datetime import date
from hashlib import sha256
import re
from time import perf_counter
from typing import Any, Iterable
from uuid import uuid4

from fastapi import APIRouter, Query, Request, Depends
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from app.core.envelope.builder import error_envelope, success_envelope
from app.core.envelope.schema import ErrorCode, RiskColor, Mode
from app.db import get_db
from app.models import KBChunk, KBDocument, KBDocumentStatus, KBParseQuality

router = APIRouter(tags=["kb"])

WORD_RE = re.compile(r"\b\w+\b")
INSTRUCTION_PATTERNS = (
    "ignore previous instructions",
    "disregard previous instructions",
    "system prompt",
    "you are chatgpt",
    "do anything now",
    "jailbreak",
)


class KBUploadJsonIn(BaseModel):
    title: str
    doc_version_date: str | None = None
    text: str
    source_url: str | None = None
    meta: dict[str, Any] | None = None


class KBSearchIn(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    include_draft: bool = False


class KBActivateIn(BaseModel):
    doc_id: str


def _get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        return request_id
    header_id = request.headers.get("X-Request-ID")
    if header_id:
        return header_id
    return f"rid-{uuid4().hex[:8]}"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _hash_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _contains_instruction_like_text(text: str) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in INSTRUCTION_PATTERNS)


def _assess_parse_quality(text: str, parse_notes: list[str]) -> str:
    stripped = text.strip()
    if len(stripped) < 300:
        parse_notes.append("text_too_short")
        return KBParseQuality.BAD.value
    return KBParseQuality.GOOD.value


def _word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def _merge_small_tail(chunks: list[str], min_words: int, max_words: int) -> list[str]:
    if len(chunks) < 2:
        return chunks
    last_count = _word_count(chunks[-1])
    if last_count < min_words:
        prev_count = _word_count(chunks[-2])
        if prev_count + last_count <= max_words:
            chunks[-2] = f"{chunks[-2].strip()}\n\n{chunks[-1].strip()}".strip()
            chunks.pop()
    return chunks


def _chunk_by_words(words: list[str], min_words: int, max_words: int, overlap: int) -> list[str]:
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    step = max_words - overlap
    if step <= 0:
        step = max_words
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words).strip())
        if end >= len(words):
            break
        start += step
    return _merge_small_tail(chunks, min_words, max_words)


def _chunk_text(text: str, min_words: int = 300, max_words: int = 800, overlap: int = 80) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []
    para_word_counts = [_word_count(p) for p in paragraphs]
    if any(count > max_words for count in para_word_counts):
        return _chunk_by_words(WORD_RE.findall(text), min_words, max_words, overlap)

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    overlap_words: list[str] = []
    for paragraph, count in zip(paragraphs, para_word_counts):
        if current and current_words + count > max_words:
            base_chunk = "\n\n".join(current).strip()
            chunk_text = base_chunk
            if overlap_words:
                chunk_text = " ".join(overlap_words) + "\n\n" + chunk_text
            chunks.append(chunk_text.strip())
            base_words = WORD_RE.findall(base_chunk)
            overlap_words = base_words[-overlap:] if overlap > 0 else []
            current = []
            current_words = 0
        current.append(paragraph)
        current_words += count
    if current:
        base_chunk = "\n\n".join(current).strip()
        chunk_text = base_chunk
        if overlap_words:
            chunk_text = " ".join(overlap_words) + "\n\n" + chunk_text
        chunks.append(chunk_text.strip())
    return _merge_small_tail(chunks, min_words, max_words)


def _score_text(query: str, text: str) -> float:
    if not query or not text:
        return 0.0
    query_tokens = [token.lower() for token in WORD_RE.findall(query) if token.strip()]
    if not query_tokens:
        return 0.0
    lowered = text.lower()
    hits = sum(lowered.count(token) for token in query_tokens)
    word_count = max(1, _word_count(text))
    return hits / word_count


def _search_condition(column, query: str):
    pattern = f"%{query.lower()}%"
    return func.lower(column).like(pattern)


def _iter_chunk_stats(chunks: Iterable[str]) -> tuple[int, float]:
    counts = [_word_count(chunk) for chunk in chunks]
    if not counts:
        return 0, 0.0
    return len(counts), sum(counts) / len(counts)


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
            mode=Mode.draft,
        )


@router.post("/kb/upload")
def kb_upload(body: KBUploadJsonIn, request: Request, db: Session = Depends(get_db)):
    start = perf_counter()
    request_id = _get_request_id(request)

    try:
        title = body.title
        doc_version_date = _parse_date(body.doc_version_date)
        source_url = body.source_url
        meta = body.meta
        text_value = body.text or ""

        doc_hash = _hash_bytes(text_value.encode("utf-8"))
        existing = db.execute(
            select(KBDocument).where(KBDocument.doc_hash == doc_hash)
        ).scalar_one_or_none()
        if existing:
            latency_ms = int((perf_counter() - start) * 1000)
            return success_envelope(
                client_message="already_ingested",
                request_id=request_id,
                latency_ms=latency_ms,
                sources=[],
                manager_note=f"doc_id={existing.id}",
                mode=Mode.draft,
            )

        doc_id = str(uuid4())
        parse_notes: list[str] = []
        contains_instructions = _contains_instruction_like_text(text_value)
        parse_quality = _assess_parse_quality(text_value, parse_notes)
        if contains_instructions and parse_quality == KBParseQuality.GOOD.value:
            parse_quality = KBParseQuality.WARN.value
            parse_notes.append("instruction_like_text")

        chunks_text = _chunk_text(text_value)
        chunk_count, avg_words = _iter_chunk_stats(chunks_text)

        doc = KBDocument(
            id=doc_id,
            title=title or "Untitled",
            doc_version_date=doc_version_date,
            status=KBDocumentStatus.DRAFT.value,
            source_url=source_url,
            storage_url=None,
            doc_hash=doc_hash,
            parse_quality=parse_quality,
            parse_notes="; ".join(parse_notes) if parse_notes else None,
            contains_instructions=contains_instructions,
            meta=meta,
        )
        db.add(doc)

        for idx, chunk_text in enumerate(chunks_text):
            chunk = KBChunk(
                id=str(uuid4()),
                doc_id=doc_id,
                section=f"Chunk {idx + 1}",
                text=chunk_text,
                order=idx,
                chunk_ref=f"kb://doc/{doc_id}#chunk-{idx}",
            )
            db.add(chunk)

        db.commit()

        recommendation = "ok"
        if parse_quality == KBParseQuality.BAD.value:
            recommendation = "parse_quality=bad -> manual text required"
        elif parse_quality == KBParseQuality.WARN.value:
            recommendation = "parse_quality=warn -> review suggested"

        latency_ms = int((perf_counter() - start) * 1000)
        manager_note = (
            f"doc_id={doc_id} "
            f"chunks_count={chunk_count} "
            f"avg_words={avg_words:.1f} "
            f"parse_quality={parse_quality} "
            f"contains_instructions={str(contains_instructions).lower()} "
            f"recommendation={recommendation}"
        )
        return success_envelope(
            client_message="ok",
            request_id=request_id,
            latency_ms=latency_ms,
            sources=[],
            manager_note=manager_note,
            mode=Mode.draft,
        )
    except (ValidationError, ValueError) as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return error_envelope(
            client_message="validation_error",
            request_id=request_id,
            latency_ms=latency_ms,
            error_code=ErrorCode.VALIDATION_ERROR,
            debug_message=str(exc),
            sources=[],
            mode=Mode.draft,
        )
    except Exception as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return success_envelope(
            client_message="error",
            request_id=request_id,
            latency_ms=latency_ms,
            sources=[],
            requires_review=True,
            requires_review_reason="activation requires review",
            risk_color=RiskColor.yellow,
            risk_reason="kb activate error",
            manager_note=f"activation error: {exc}",
            mode=Mode.draft,
        )


@router.post("/kb/search")
def kb_search(body: KBSearchIn, request: Request, db: Session = Depends(get_db)):
    start = perf_counter()
    request_id = _get_request_id(request)

    try:
        query = body.query.strip()
        if not query:
            latency_ms = int((perf_counter() - start) * 1000)
            return success_envelope(
                client_message="ok",
                request_id=request_id,
                latency_ms=latency_ms,
                sources=[],
                data=[],
                manager_note="empty_query",
                mode=Mode.draft,
            )

        statuses = [KBDocumentStatus.ACTIVE.value]
        if body.include_draft:
            statuses.append(KBDocumentStatus.DRAFT.value)

        condition = _search_condition(KBChunk.text, query)

        stmt = (
            select(KBChunk, KBDocument)
            .join(KBDocument, KBChunk.doc_id == KBDocument.id)
            .where(condition)
            .where(KBDocument.status.in_(statuses))
            .limit(max(50, body.top_k * 5))
        )
        rows = db.execute(stmt).all()

        results = []
        for chunk, doc in rows:
            score = _score_text(query, chunk.text)
            if score <= 0:
                continue
            results.append(
                {
                    "chunk_ref": chunk.chunk_ref,
                    "text": chunk.text,
                    "section": chunk.section,
                    "doc_id": doc.id,
                    "doc_title": doc.title,
                    "doc_version_date": doc.doc_version_date.isoformat() if doc.doc_version_date else None,
                    "score": float(score),
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        results = results[: body.top_k]

        latency_ms = int((perf_counter() - start) * 1000)
        return success_envelope(
            client_message="ok",
            request_id=request_id,
            latency_ms=latency_ms,
            sources=[],
            data=results,
            mode=Mode.draft,
        )
    except Exception as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return error_envelope(
            client_message="error",
            request_id=request_id,
            latency_ms=latency_ms,
            error_code=ErrorCode.INTERNAL_ERROR,
            debug_message=str(exc),
            sources=[],
            mode=Mode.draft,
        )


@router.post("/kb/activate")
def kb_activate(body: KBActivateIn, request: Request, db: Session = Depends(get_db)):
    start = perf_counter()
    request_id = _get_request_id(request)

    try:
        doc = db.get(KBDocument, body.doc_id)
        if not doc:
            latency_ms = int((perf_counter() - start) * 1000)
            return success_envelope(
                client_message="not_found",
                request_id=request_id,
                latency_ms=latency_ms,
                sources=[],
                requires_review=True,
                requires_review_reason="activation requires review",
                risk_color=RiskColor.yellow,
                risk_reason="doc_id not found",
                manager_note="activation blocked: doc_id not found",
                mode=Mode.draft,
            )

        if doc.parse_quality == KBParseQuality.BAD.value:
            latency_ms = int((perf_counter() - start) * 1000)
            return success_envelope(
                client_message="cannot_activate_bad_parse_quality",
                request_id=request_id,
                latency_ms=latency_ms,
                sources=[],
                requires_review=True,
                requires_review_reason="activation requires review",
                risk_color=RiskColor.yellow,
                risk_reason="parse_quality=bad",
                manager_note="activation blocked: parse_quality=bad",
                mode=Mode.draft,
            )

        archived = db.execute(
            update(KBDocument)
            .where(KBDocument.title == doc.title)
            .where(KBDocument.id != doc.id)
            .where(KBDocument.status == KBDocumentStatus.ACTIVE.value)
            .values(status=KBDocumentStatus.ARCHIVED.value)
        )
        doc.status = KBDocumentStatus.ACTIVE.value
        db.commit()

        latency_ms = int((perf_counter() - start) * 1000)
        manager_note = f"activated_doc_id={doc.id} archived_count={archived.rowcount or 0}"
        return success_envelope(
            client_message="ok",
            request_id=request_id,
            latency_ms=latency_ms,
            sources=[],
            requires_review=True,
            requires_review_reason="activation requires review",
            risk_color=RiskColor.yellow,
            risk_reason="kb activate hitl",
            manager_note=manager_note,
            mode=Mode.draft,
        )
    except Exception as exc:
        latency_ms = int((perf_counter() - start) * 1000)
        return error_envelope(
            client_message="error",
            request_id=request_id,
            latency_ms=latency_ms,
            error_code=ErrorCode.INTERNAL_ERROR,
            debug_message=str(exc),
            sources=[],
            mode=Mode.draft,
        )
