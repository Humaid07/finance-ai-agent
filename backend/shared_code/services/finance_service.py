"""
Finance reporting service.
Computes trial balance, P&L, revenue, expenses, net income, and journal analytics.
All methods operate on structured data — no LLM hallucination risk.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from shared_code.models.hierarchy import GLAccount, AccountGroup, Ledger
from shared_code.models.transactions import JournalEntry, JournalLine

logger = logging.getLogger(__name__)


@dataclass
class TrialBalanceRow:
    account_code: str
    account_name: str
    account_type: str
    debit: float
    credit: float
    balance: float


@dataclass
class PnLResult:
    revenue: float
    expenses: float
    net_income: float
    revenue_breakdown: list[dict]
    expense_breakdown: list[dict]
    period: str


@dataclass
class DashboardData:
    total_revenue: float
    total_expenses: float
    net_income: float
    journal_entry_count: int
    journal_line_count: int
    top_expense_accounts: list[dict]
    revenue_by_period: list[dict]


def _to_float(val) -> float:
    """Safe conversion of Decimal/None to float."""
    if val is None:
        return 0.0
    return float(val)


class FinanceService:
    def __init__(self, session: Session):
        self.session = session

    def get_trial_balance(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        ledger_id: str | None = None,
    ) -> list[TrialBalanceRow]:
        """
        Aggregate journal lines by GL account to produce a trial balance.
        Returns debit total, credit total, and net balance per account.
        """
        query = (
            self.session.query(
                GLAccount.code,
                GLAccount.name,
                GLAccount.account_type,
                func.coalesce(func.sum(JournalLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalLine.credit), 0).label("total_credit"),
            )
            .join(JournalLine, JournalLine.account_id == GLAccount.id)
            .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        )

        filters = [JournalEntry.status == "POSTED"]
        if date_from:
            filters.append(JournalLine.posting_date >= date_from)
        if date_to:
            filters.append(JournalLine.posting_date <= date_to)
        if ledger_id:
            filters.append(JournalLine.ledger_id == ledger_id)

        query = query.filter(and_(*filters))
        query = query.group_by(GLAccount.code, GLAccount.name, GLAccount.account_type)
        query = query.order_by(GLAccount.code)

        rows = []
        for code, name, acct_type, debit, credit in query.all():
            d = _to_float(debit)
            c = _to_float(credit)
            # Normal balance: ASSET/EXPENSE = debit-credit; LIABILITY/EQUITY/REVENUE = credit-debit
            if acct_type in ("ASSET", "EXPENSE"):
                balance = d - c
            else:
                balance = c - d
            rows.append(
                TrialBalanceRow(
                    account_code=code,
                    account_name=name,
                    account_type=acct_type,
                    debit=d,
                    credit=c,
                    balance=balance,
                )
            )
        return rows

    def get_pnl(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        ledger_id: str | None = None,
    ) -> PnLResult:
        """Compute P&L from journal lines grouped by account type."""
        tb = self.get_trial_balance(date_from, date_to, ledger_id)

        revenue_rows = [r for r in tb if r.account_type == "REVENUE"]
        expense_rows = [r for r in tb if r.account_type == "EXPENSE"]

        total_revenue = sum(r.balance for r in revenue_rows)
        total_expenses = sum(r.balance for r in expense_rows)

        period = ""
        if date_from:
            period = date_from.strftime("%Y-%m")

        return PnLResult(
            revenue=total_revenue,
            expenses=total_expenses,
            net_income=total_revenue - total_expenses,
            revenue_breakdown=[
                {"account": r.account_name, "amount": r.balance} for r in revenue_rows
            ],
            expense_breakdown=[
                {"account": r.account_name, "amount": r.balance} for r in expense_rows
            ],
            period=period,
        )

    def get_account_balance(self, account_name: str) -> dict:
        """
        Look up balance for a specific account by name or code (case-insensitive partial match).
        """
        account = (
            self.session.query(GLAccount)
            .filter(
                or_(
                    GLAccount.name.ilike(f"%{account_name}%"),
                    GLAccount.code.ilike(f"%{account_name}%"),
                )
            )
            .first()
        )
        if not account:
            return {"account": account_name, "balance": 0.0, "found": False}

        result = (
            self.session.query(
                func.coalesce(func.sum(JournalLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalLine.credit), 0).label("total_credit"),
            )
            .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
            .filter(
                JournalLine.account_id == account.id,
                JournalEntry.status == "POSTED",
            )
            .one()
        )

        d = _to_float(result.total_debit)
        c = _to_float(result.total_credit)
        balance = d - c if account.account_type in ("ASSET", "EXPENSE") else c - d

        return {
            "account_code": account.code,
            "account_name": account.name,
            "account_type": account.account_type,
            "debit": d,
            "credit": c,
            "balance": balance,
            "found": True,
        }

    def get_top_expenses(self, limit: int = 5) -> list[dict]:
        """Return the top N expense accounts by balance."""
        tb = self.get_trial_balance()
        expense_rows = sorted(
            [r for r in tb if r.account_type == "EXPENSE"],
            key=lambda r: r.balance,
            reverse=True,
        )
        return [
            {
                "account_code": r.account_code,
                "account_name": r.account_name,
                "balance": r.balance,
            }
            for r in expense_rows[:limit]
        ]

    def get_journal_lines(
        self,
        date_from: date | None = None,
        date_to: date | None = None,
        account_id: str | None = None,
        cost_center_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Paginated journal line retrieval with optional filters."""
        query = (
            self.session.query(JournalLine)
            .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
        )

        filters = [JournalEntry.status == "POSTED"]
        if date_from:
            filters.append(JournalLine.posting_date >= date_from)
        if date_to:
            filters.append(JournalLine.posting_date <= date_to)
        if account_id:
            filters.append(JournalLine.account_id == account_id)
        if cost_center_id:
            filters.append(JournalLine.cost_center_id == cost_center_id)

        query = query.filter(and_(*filters))
        total = query.count()

        lines = (
            query.order_by(JournalLine.posting_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "items": [self._serialize_journal_line(line) for line in lines],
        }

    def get_journal_entries(self, page: int = 1, page_size: int = 50) -> dict:
        """Paginated journal entry retrieval."""
        query = self.session.query(JournalEntry).filter(JournalEntry.status == "POSTED")
        total = query.count()
        entries = (
            query.order_by(JournalEntry.posting_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "items": [self._serialize_journal_entry(e) for e in entries],
        }

    def get_dashboard(self) -> DashboardData:
        """Aggregate key metrics for the dashboard."""
        pnl = self.get_pnl()
        je_count = self.session.query(func.count(JournalEntry.id)).scalar() or 0
        jl_count = self.session.query(func.count(JournalLine.id)).scalar() or 0
        top_expenses = self.get_top_expenses(5)

        # Revenue by period (last 6 months)
        revenue_by_period_query = (
            self.session.query(
                JournalEntry.period,
                func.coalesce(func.sum(JournalLine.credit), 0).label("revenue"),
            )
            .join(JournalLine, JournalLine.journal_entry_id == JournalEntry.id)
            .join(GLAccount, GLAccount.id == JournalLine.account_id)
            .filter(
                GLAccount.account_type == "REVENUE",
                JournalEntry.status == "POSTED",
            )
            .group_by(JournalEntry.period)
            .order_by(JournalEntry.period)
            .limit(12)
            .all()
        )

        return DashboardData(
            total_revenue=pnl.revenue,
            total_expenses=pnl.expenses,
            net_income=pnl.net_income,
            journal_entry_count=je_count,
            journal_line_count=jl_count,
            top_expense_accounts=top_expenses,
            revenue_by_period=[
                {"period": p, "revenue": _to_float(r)} for p, r in revenue_by_period_query
            ],
        )

    def explain_variance(
        self, account_name: str, period_1: str, period_2: str
    ) -> dict:
        """
        Compare account balance between two periods and explain the variance.
        Periods in YYYY-MM format.
        """
        def get_period_balance(period: str) -> float:
            year, month = period.split("-")
            from_date = date(int(year), int(month), 1)
            import calendar
            last_day = calendar.monthrange(int(year), int(month))[1]
            to_date = date(int(year), int(month), last_day)
            result = self.get_account_balance(account_name)
            # For period-specific: filter by date range
            account = (
                self.session.query(GLAccount)
                .filter(GLAccount.name.ilike(f"%{account_name}%"))
                .first()
            )
            if not account:
                return 0.0
            r = (
                self.session.query(
                    func.coalesce(func.sum(JournalLine.debit), 0),
                    func.coalesce(func.sum(JournalLine.credit), 0),
                )
                .join(JournalEntry, JournalEntry.id == JournalLine.journal_entry_id)
                .filter(
                    JournalLine.account_id == account.id,
                    JournalLine.posting_date >= from_date,
                    JournalLine.posting_date <= to_date,
                    JournalEntry.status == "POSTED",
                )
                .one()
            )
            d, c = _to_float(r[0]), _to_float(r[1])
            return d - c if account.account_type in ("ASSET", "EXPENSE") else c - d

        bal1 = get_period_balance(period_1)
        bal2 = get_period_balance(period_2)
        variance = bal2 - bal1
        pct = (variance / bal1 * 100) if bal1 else 0

        return {
            "account": account_name,
            "period_1": period_1,
            "period_1_balance": bal1,
            "period_2": period_2,
            "period_2_balance": bal2,
            "variance": variance,
            "variance_pct": round(pct, 2),
        }

    def get_hierarchy_tree(self) -> list[dict]:
        """Return the full GL hierarchy as a tree structure."""
        from shared_code.models.hierarchy import Company, Entity, Ledger, AccountGroup
        companies = self.session.query(Company).all()
        result = []
        for company in companies:
            c_node = {
                "id": str(company.id),
                "code": company.code,
                "name": company.name,
                "type": "company",
                "children": [],
            }
            for entity in company.entities:
                e_node = {
                    "id": str(entity.id),
                    "code": entity.code,
                    "name": entity.name,
                    "type": "entity",
                    "children": [],
                }
                for ledger in entity.ledgers:
                    l_node = {
                        "id": str(ledger.id),
                        "code": ledger.code,
                        "name": ledger.name,
                        "type": "ledger",
                        "children": [],
                    }
                    for ag in ledger.account_groups:
                        ag_node = {
                            "id": str(ag.id),
                            "code": ag.code,
                            "name": ag.name,
                            "type": "account_group",
                            "account_type": ag.account_type,
                            "children": [
                                {
                                    "id": str(acct.id),
                                    "code": acct.code,
                                    "name": acct.name,
                                    "type": "gl_account",
                                    "account_type": acct.account_type,
                                }
                                for acct in ag.gl_accounts
                            ],
                        }
                        l_node["children"].append(ag_node)
                    e_node["children"].append(l_node)
                c_node["children"].append(e_node)
            result.append(c_node)
        return result

    def _serialize_journal_line(self, line: JournalLine) -> dict:
        return {
            "id": str(line.id),
            "journal_entry_id": str(line.journal_entry_id),
            "account_id": str(line.account_id),
            "account_name": line.account.name if line.account else None,
            "account_code": line.account.code if line.account else None,
            "debit": _to_float(line.debit),
            "credit": _to_float(line.credit),
            "posting_date": line.posting_date.isoformat(),
            "description": line.description,
            "document_reference": line.document_reference,
            "currency_code": line.currency_code,
        }

    def _serialize_journal_entry(self, entry: JournalEntry) -> dict:
        return {
            "id": str(entry.id),
            "entry_number": entry.entry_number,
            "description": entry.description,
            "posting_date": entry.posting_date.isoformat(),
            "period": entry.period,
            "status": entry.status,
            "document_reference": entry.document_reference,
            "line_count": len(entry.lines),
        }
