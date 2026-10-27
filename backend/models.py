"""Persistent users and saved email analyses."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    analyzed_emails: Mapped[list["AnalyzedEmail"]] = relationship(
        back_populates="user", passive_deletes="all"
    )


class AnalyzedEmail(Base):
    __tablename__ = "analyzed_emails"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_analyzed_emails_confidence_range"),
        CheckConstraint(
            "analysis_mode IS NULL OR analysis_mode IN ('mock', 'real', 'unknown')",
            name="ck_analyzed_emails_analysis_mode",
        ),
        Index("ix_analyzed_emails_user_created_at", "user_id", "created_at"),
        UniqueConstraint(
            "user_id",
            "idempotency_key",
            name="uq_analyzed_emails_user_idempotency_key",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    prediction: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    risk_level: Mapped[str | None] = mapped_column(String(20))
    indicators: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    explanation: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)

    analysis_mode: Mapped[str | None] = mapped_column(String(20))
    analysis_provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="analyzed_emails")
