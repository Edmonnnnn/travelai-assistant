from __future__ import annotations

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from app.db import Base


class KBDocumentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class KBParseQuality(str, Enum):
    GOOD = "good"
    WARN = "warn"
    BAD = "bad"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)


class KBDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(String(36), primary_key=True)
    title = Column(String, nullable=False)
    doc_version_date = Column(Date, nullable=True)
    ingested_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    status = Column(
        String,
        nullable=False,
        default=KBDocumentStatus.DRAFT.value,
        server_default=text("'draft'"),
    )
    source_url = Column(String, nullable=True)
    storage_url = Column(String, nullable=True)
    doc_hash = Column(String, nullable=False)
    parse_quality = Column(
        String,
        nullable=False,
        default=KBParseQuality.GOOD.value,
        server_default=text("'good'"),
    )
    parse_notes = Column(Text, nullable=True)
    contains_instructions = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
    meta = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)

    chunks = relationship(
        "KBChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_kb_documents_doc_hash", "doc_hash", unique=True),
        Index("ix_kb_documents_status", "status"),
        Index("ix_kb_documents_doc_version_date", "doc_version_date"),
    )


class KBChunk(Base):
    __tablename__ = "kb_chunks"

    id = Column(String(36), primary_key=True)
    doc_id = Column(
        String(36),
        ForeignKey("kb_documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    section = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    chunk_ref = Column(String, nullable=False)
    page = Column(Integer, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    embedding = Column(JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=True)

    document = relationship("KBDocument", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("doc_id", "order", name="uq_kb_chunks_doc_id_order"),
        Index("ix_kb_chunks_doc_id", "doc_id"),
        Index("ix_kb_chunks_chunk_ref", "chunk_ref", unique=True),
    )
