"""
Journal Entry and Journal Line SQLAlchemy models.
These are the core transactional tables in the GL system.
"""
import uuid
from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_code.models.base import Base


class JournalEntry(Base):
    """Journal entry header - groups related journal lines."""
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledgers.id"), nullable=False
    )
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    posting_date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    status: Mapped[str] = mapped_column(String(20), default="POSTED")  # DRAFT, POSTED, REVERSED
    document_reference: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str | None] = mapped_column(String(50))  # MANUAL, IMPORT, SYSTEM
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_by: Mapped[str | None] = mapped_column(String(100))

    lines: Mapped[list["JournalLine"]] = relationship(
        "JournalLine", back_populates="journal_entry"
    )

    __table_args__ = (
        Index("ix_je_posting_date", "posting_date"),
        Index("ix_je_period", "period"),
        Index("ix_je_entity", "entity_id"),
        Index("ix_je_ledger", "ledger_id"),
        Index("ix_je_number", "entry_number"),
    )


class JournalLine(Base):
    """
    Individual debit/credit line within a journal entry.
    Supports full GL dimension tagging.
    """
    __tablename__ = "journal_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gl_accounts.id"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledgers.id"), nullable=False
    )
    # Optional dimensions
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cost_centers.id")
    )
    profit_center_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profit_centers.id")
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id")
    )
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id")
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id")
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id")
    )
    # Amounts
    debit: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0, nullable=False)
    credit: Mapped[float] = mapped_column(Numeric(18, 2), default=0.0, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    # Description and reference
    description: Mapped[str | None] = mapped_column(Text)
    document_reference: Mapped[str | None] = mapped_column(String(100))
    posting_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship(
        "JournalEntry", back_populates="lines"
    )
    account: Mapped["GLAccount"] = relationship("GLAccount", back_populates="journal_lines")

    __table_args__ = (
        Index("ix_jl_account", "account_id"),
        Index("ix_jl_posting_date", "posting_date"),
        Index("ix_jl_entity", "entity_id"),
        Index("ix_jl_cost_center", "cost_center_id"),
        Index("ix_jl_journal_entry", "journal_entry_id"),
    )
