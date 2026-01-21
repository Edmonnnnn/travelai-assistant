"""A3: kb documents and chunks

Revision ID: a3b1c2d3e4f5
Revises: 7f1111503c29
Create Date: 2026-01-21 17:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a3b1c2d3e4f5"
down_revision: Union[str, None] = "7f1111503c29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.create_table(
        "kb_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("doc_version_date", sa.Date(), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("storage_url", sa.String(), nullable=True),
        sa.Column("doc_hash", sa.String(), nullable=False),
        sa.Column(
            "parse_quality",
            sa.String(),
            nullable=False,
            server_default=sa.text("'good'"),
        ),
        sa.Column("parse_notes", sa.Text(), nullable=True),
        sa.Column(
            "contains_instructions",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("meta", json_type, nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_kb_documents_doc_hash",
        "kb_documents",
        ["doc_hash"],
        unique=True,
    )
    op.create_index(
        "ix_kb_documents_status",
        "kb_documents",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_kb_documents_doc_version_date",
        "kb_documents",
        ["doc_version_date"],
        unique=False,
    )

    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "doc_id",
            sa.String(length=36),
            sa.ForeignKey("kb_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.String(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("chunk_ref", sa.String(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("embedding", json_type, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id", "order", name="uq_kb_chunks_doc_id_order"),
    )
    op.create_index(
        "ix_kb_chunks_doc_id",
        "kb_chunks",
        ["doc_id"],
        unique=False,
    )
    op.create_index(
        "ix_kb_chunks_chunk_ref",
        "kb_chunks",
        ["chunk_ref"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_kb_chunks_chunk_ref", table_name="kb_chunks")
    op.drop_index("ix_kb_chunks_doc_id", table_name="kb_chunks")
    op.drop_table("kb_chunks")
    op.drop_index("ix_kb_documents_doc_version_date", table_name="kb_documents")
    op.drop_index("ix_kb_documents_status", table_name="kb_documents")
    op.drop_index("ix_kb_documents_doc_hash", table_name="kb_documents")
    op.drop_table("kb_documents")
