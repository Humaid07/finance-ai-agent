"""
GL Hierarchy SQLAlchemy models.
Enterprise accounting hierarchy:
  Company → Entity → Ledger → AccountGroup → GLAccount → SubAccount
  CostCenter, ProfitCenter, Project, Region, Vendor, Customer
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_code.models.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Company(TimestampMixin, Base):
    """Top-level enterprise entity."""
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    entities: Mapped[list["Entity"]] = relationship("Entity", back_populates="company")

    __table_args__ = (Index("ix_companies_code", "code"),)


class Entity(TimestampMixin, Base):
    """Legal entity within a company."""
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(3))
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company: Mapped["Company"] = relationship("Company", back_populates="entities")
    ledgers: Mapped[list["Ledger"]] = relationship("Ledger", back_populates="entity")

    __table_args__ = (Index("ix_entities_code", "code"),)


class Ledger(TimestampMixin, Base):
    """Financial ledger belonging to a legal entity."""
    __tablename__ = "ledgers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ledger_type: Mapped[str] = mapped_column(String(50), default="ACTUAL")  # ACTUAL, BUDGET, FORECAST
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="ledgers")
    account_groups: Mapped[list["AccountGroup"]] = relationship(
        "AccountGroup", back_populates="ledger"
    )

    __table_args__ = (Index("ix_ledgers_code", "code"),)


class AccountGroup(TimestampMixin, Base):
    """Groups of GL accounts (e.g. Assets, Liabilities, Revenue, Expenses)."""
    __tablename__ = "account_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledgers.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    normal_balance: Mapped[str] = mapped_column(String(6), default="DEBIT")  # DEBIT or CREDIT
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    ledger: Mapped["Ledger"] = relationship("Ledger", back_populates="account_groups")
    gl_accounts: Mapped[list["GLAccount"]] = relationship(
        "GLAccount", back_populates="account_group"
    )

    __table_args__ = (
        Index("ix_account_groups_code", "code"),
        Index("ix_account_groups_ledger", "ledger_id"),
    )


class GLAccount(TimestampMixin, Base):
    """General Ledger account."""
    __tablename__ = "gl_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account_groups.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    normal_balance: Mapped[str] = mapped_column(String(6), default="DEBIT")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    allows_direct_posting: Mapped[bool] = mapped_column(Boolean, default=True)

    account_group: Mapped["AccountGroup"] = relationship(
        "AccountGroup", back_populates="gl_accounts"
    )
    journal_lines: Mapped[list["JournalLine"]] = relationship(
        "JournalLine", back_populates="account"
    )

    __table_args__ = (
        Index("ix_gl_accounts_code", "code"),
        Index("ix_gl_accounts_type", "account_type"),
    )


class CostCenter(TimestampMixin, Base):
    """Cost center for expense allocation."""
    __tablename__ = "cost_centers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    manager: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_cost_centers_code", "code"),)


class ProfitCenter(TimestampMixin, Base):
    """Profit center for revenue/expense tracking."""
    __tablename__ = "profit_centers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_profit_centers_code", "code"),)


class Project(TimestampMixin, Base):
    """Project for project-based accounting."""
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    budget: Mapped[float | None] = mapped_column(Numeric(18, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_projects_code", "code"),)


class Region(TimestampMixin, Base):
    """Geographic region for segmented reporting."""
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    __table_args__ = (Index("ix_regions_code", "code"),)


class Vendor(TimestampMixin, Base):
    """Vendor/supplier master."""
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_vendors_code", "code"),)


class Customer(TimestampMixin, Base):
    """Customer master."""
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_customers_code", "code"),)
