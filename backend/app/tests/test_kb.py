from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import KBChunk, KBDocument, KBDocumentStatus, KBParseQuality


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def client(db_session_factory):
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_upload_same_text_twice(client, db_session_factory):
    text = ("word " * 350).strip()
    payload = {
        "title": "Test Doc",
        "doc_version_date": "2026-01-01",
        "text": text,
    }

    resp = client.post("/kb/upload", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True

    db = db_session_factory()
    try:
        chunks_before = db.query(KBChunk).count()
        assert chunks_before > 0

        resp_dup = client.post("/kb/upload", json=payload)
        dup_body = resp_dup.json()
        assert dup_body["client_message"] == "already_ingested"

        chunks_after = db.query(KBChunk).count()
        assert chunks_after == chunks_before
    finally:
        db.close()


def test_activate_bad_parse_quality(client, db_session_factory):
    db = db_session_factory()
    try:
        doc_id = str(uuid4())
        doc = KBDocument(
            id=doc_id,
            title="Bad Doc",
            status=KBDocumentStatus.DRAFT.value,
            doc_hash=uuid4().hex,
            parse_quality=KBParseQuality.BAD.value,
            contains_instructions=False,
        )
        db.add(doc)
        db.commit()

        resp = client.post("/kb/activate", json={"doc_id": doc_id})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["requires_review"] is True

        db.refresh(doc)
        assert doc.status == KBDocumentStatus.DRAFT.value
    finally:
        db.close()


def test_search_excludes_draft(client, db_session_factory):
    db = db_session_factory()
    try:
        doc_id = str(uuid4())
        doc = KBDocument(
            id=doc_id,
            title="Draft Doc",
            status=KBDocumentStatus.DRAFT.value,
            doc_hash=uuid4().hex,
            parse_quality=KBParseQuality.GOOD.value,
            contains_instructions=False,
        )
        db.add(doc)
        db.add(
            KBChunk(
                id=str(uuid4()),
                doc_id=doc_id,
                section="Chunk 1",
                text="draftonly term appears here",
                order=0,
                chunk_ref=f"kb://doc/{doc_id}#chunk-0",
            )
        )
        db.commit()

        resp = client.post("/kb/search", json={"query": "draftonly", "top_k": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body.get("data") == []

        resp_include = client.post(
            "/kb/search",
            json={"query": "draftonly", "top_k": 5, "include_draft": True},
        )
        assert resp_include.status_code == 200
        body_include = resp_include.json()
        assert body_include["ok"] is True
        assert len(body_include.get("data") or []) == 1
    finally:
        db.close()
