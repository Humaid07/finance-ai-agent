"""
Seeds the database with sample finance data.
Creates a complete GL hierarchy with sample journal entries.

Usage:
    cd backend
    python ../scripts/seed_data.py
"""
import sys
import os
import uuid
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from shared_code.database import get_db_session
from shared_code.models import (
    Base,
    Company,
    Entity,
    Ledger,
    AccountGroup,
    GLAccount,
    CostCenter,
    ProfitCenter,
    Project,
    Region,
    Vendor,
    Customer,
    JournalEntry,
    JournalLine,
)
from shared_code.database import get_engine


def create_schema():
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Schema ensured.")


def seed():
    create_schema()

    with get_db_session() as session:
        # ── Company ─────────────────────────────────────────────────────────
        company = Company(
            id=uuid.uuid4(),
            code="ACME",
            name="ACME Corporation",
            description="Sample enterprise company for demo",
        )
        session.add(company)
        session.flush()

        # ── Entity ───────────────────────────────────────────────────────────
        entity = Entity(
            id=uuid.uuid4(),
            company_id=company.id,
            code="US01",
            name="ACME United States",
            country_code="USA",
            currency_code="USD",
        )
        session.add(entity)
        session.flush()

        # ── Ledger ───────────────────────────────────────────────────────────
        ledger = Ledger(
            id=uuid.uuid4(),
            entity_id=entity.id,
            code="ACTUAL",
            name="Actual Ledger",
            ledger_type="ACTUAL",
            currency_code="USD",
        )
        session.add(ledger)
        session.flush()

        # ── Cost Centers ─────────────────────────────────────────────────────
        cc_ops = CostCenter(id=uuid.uuid4(), entity_id=entity.id, code="CC-OPS", name="Operations")
        cc_sales = CostCenter(id=uuid.uuid4(), entity_id=entity.id, code="CC-SALES", name="Sales")
        cc_admin = CostCenter(id=uuid.uuid4(), entity_id=entity.id, code="CC-ADMIN", name="Administration")
        session.add_all([cc_ops, cc_sales, cc_admin])

        # ── Profit Centers ───────────────────────────────────────────────────
        pc_product = ProfitCenter(id=uuid.uuid4(), entity_id=entity.id, code="PC-PROD", name="Product Revenue")
        pc_services = ProfitCenter(id=uuid.uuid4(), entity_id=entity.id, code="PC-SVC", name="Services Revenue")
        session.add_all([pc_product, pc_services])

        # ── Projects ─────────────────────────────────────────────────────────
        proj_alpha = Project(
            id=uuid.uuid4(),
            entity_id=entity.id,
            code="PROJ-ALPHA",
            name="Project Alpha",
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 12, 31),
            budget=500000.00,
        )
        session.add(proj_alpha)

        # ── Region ───────────────────────────────────────────────────────────
        region_na = Region(id=uuid.uuid4(), code="NA", name="North America")
        session.add(region_na)

        # ── Vendors ──────────────────────────────────────────────────────────
        vendor_aws = Vendor(id=uuid.uuid4(), entity_id=entity.id, code="V-AWS", name="Amazon Web Services")
        vendor_travel = Vendor(id=uuid.uuid4(), entity_id=entity.id, code="V-TRAVEL", name="Corporate Travel Inc")
        session.add_all([vendor_aws, vendor_travel])

        # ── Customers ────────────────────────────────────────────────────────
        cust_bigcorp = Customer(id=uuid.uuid4(), entity_id=entity.id, code="C-BIGCORP", name="BigCorp Ltd")
        cust_techco = Customer(id=uuid.uuid4(), entity_id=entity.id, code="C-TECHCO", name="TechCo Inc")
        session.add_all([cust_bigcorp, cust_techco])
        session.flush()

        # ── Account Groups ───────────────────────────────────────────────────
        ag_assets = AccountGroup(
            id=uuid.uuid4(), ledger_id=ledger.id, code="1000",
            name="Assets", account_type="ASSET", normal_balance="DEBIT", sort_order=1
        )
        ag_liabilities = AccountGroup(
            id=uuid.uuid4(), ledger_id=ledger.id, code="2000",
            name="Liabilities", account_type="LIABILITY", normal_balance="CREDIT", sort_order=2
        )
        ag_equity = AccountGroup(
            id=uuid.uuid4(), ledger_id=ledger.id, code="3000",
            name="Equity", account_type="EQUITY", normal_balance="CREDIT", sort_order=3
        )
        ag_revenue = AccountGroup(
            id=uuid.uuid4(), ledger_id=ledger.id, code="4000",
            name="Revenue", account_type="REVENUE", normal_balance="CREDIT", sort_order=4
        )
        ag_expenses = AccountGroup(
            id=uuid.uuid4(), ledger_id=ledger.id, code="5000",
            name="Expenses", account_type="EXPENSE", normal_balance="DEBIT", sort_order=5
        )
        session.add_all([ag_assets, ag_liabilities, ag_equity, ag_revenue, ag_expenses])
        session.flush()

        # ── GL Accounts ──────────────────────────────────────────────────────
        accts = {}

        def add_account(group, code, name, acct_type, normal="DEBIT"):
            a = GLAccount(
                id=uuid.uuid4(),
                account_group_id=group.id,
                code=code, name=name,
                account_type=acct_type,
                normal_balance=normal,
            )
            session.add(a)
            accts[code] = a
            return a

        # Assets
        add_account(ag_assets, "1010", "Cash and Cash Equivalents", "ASSET")
        add_account(ag_assets, "1020", "Accounts Receivable", "ASSET")
        add_account(ag_assets, "1030", "Prepaid Expenses", "ASSET")
        add_account(ag_assets, "1100", "Property, Plant & Equipment", "ASSET")

        # Liabilities
        add_account(ag_liabilities, "2010", "Accounts Payable", "LIABILITY", "CREDIT")
        add_account(ag_liabilities, "2020", "Accrued Liabilities", "LIABILITY", "CREDIT")
        add_account(ag_liabilities, "2030", "Deferred Revenue", "LIABILITY", "CREDIT")

        # Equity
        add_account(ag_equity, "3010", "Common Stock", "EQUITY", "CREDIT")
        add_account(ag_equity, "3020", "Retained Earnings", "EQUITY", "CREDIT")

        # Revenue
        add_account(ag_revenue, "4010", "Product Revenue", "REVENUE", "CREDIT")
        add_account(ag_revenue, "4020", "Service Revenue", "REVENUE", "CREDIT")
        add_account(ag_revenue, "4030", "Other Income", "REVENUE", "CREDIT")

        # Expenses
        add_account(ag_expenses, "5010", "Salary Expense", "EXPENSE")
        add_account(ag_expenses, "5020", "Travel Expense", "EXPENSE")
        add_account(ag_expenses, "5030", "Software & Cloud Expense", "EXPENSE")
        add_account(ag_expenses, "5040", "Marketing Expense", "EXPENSE")
        add_account(ag_expenses, "5050", "Office & Admin Expense", "EXPENSE")
        add_account(ag_expenses, "5060", "Depreciation Expense", "EXPENSE")

        session.flush()

        # ── Journal Entries & Lines ──────────────────────────────────────────
        je_counter = 1

        def make_je(posting_date: date, description: str, lines_data: list[dict]) -> JournalEntry:
            nonlocal je_counter
            je = JournalEntry(
                id=uuid.uuid4(),
                entity_id=entity.id,
                ledger_id=ledger.id,
                entry_number=f"JE-2026-{je_counter:04d}",
                description=description,
                posting_date=posting_date,
                period=posting_date.strftime("%Y-%m"),
                status="POSTED",
                source="MANUAL",
            )
            je_counter += 1
            session.add(je)
            session.flush()

            for ld in lines_data:
                line = JournalLine(
                    id=uuid.uuid4(),
                    journal_entry_id=je.id,
                    account_id=accts[ld["account"]].id,
                    entity_id=entity.id,
                    ledger_id=ledger.id,
                    cost_center_id=ld.get("cc_id"),
                    profit_center_id=ld.get("pc_id"),
                    debit=ld.get("debit", 0.0),
                    credit=ld.get("credit", 0.0),
                    posting_date=posting_date,
                    description=ld.get("desc"),
                    currency_code="USD",
                )
                session.add(line)
            return je

        # January 2026
        make_je(date(2026, 1, 15), "January Product Revenue", [
            {"account": "1020", "debit": 150000.00, "desc": "AR for product sales"},
            {"account": "4010", "credit": 150000.00, "desc": "Product Revenue recognized", "pc_id": pc_product.id},
        ])
        make_je(date(2026, 1, 15), "January Service Revenue", [
            {"account": "1020", "debit": 45000.00, "desc": "AR for services"},
            {"account": "4020", "credit": 45000.00, "desc": "Service Revenue recognized", "pc_id": pc_services.id},
        ])
        make_je(date(2026, 1, 31), "January Salaries", [
            {"account": "5010", "debit": 85000.00, "desc": "Monthly salaries", "cc_id": cc_ops.id},
            {"account": "2010", "credit": 85000.00, "desc": "Salary payable"},
        ])
        make_je(date(2026, 1, 31), "January Cloud Infrastructure", [
            {"account": "5030", "debit": 12000.00, "desc": "AWS Cloud costs", "cc_id": cc_ops.id},
            {"account": "2010", "credit": 12000.00, "desc": "AWS invoice payable"},
        ])
        make_je(date(2026, 1, 28), "January Travel Expense", [
            {"account": "5020", "debit": 8500.00, "desc": "Sales team travel", "cc_id": cc_sales.id},
            {"account": "2010", "credit": 8500.00, "desc": "Travel expense payable"},
        ])

        # February 2026
        make_je(date(2026, 2, 15), "February Product Revenue", [
            {"account": "1020", "debit": 180000.00},
            {"account": "4010", "credit": 180000.00, "pc_id": pc_product.id},
        ])
        make_je(date(2026, 2, 15), "February Service Revenue", [
            {"account": "1020", "debit": 52000.00},
            {"account": "4020", "credit": 52000.00, "pc_id": pc_services.id},
        ])
        make_je(date(2026, 2, 28), "February Salaries", [
            {"account": "5010", "debit": 85000.00, "cc_id": cc_ops.id},
            {"account": "2010", "credit": 85000.00},
        ])
        make_je(date(2026, 2, 28), "February Marketing", [
            {"account": "5040", "debit": 25000.00, "cc_id": cc_sales.id},
            {"account": "2010", "credit": 25000.00},
        ])
        make_je(date(2026, 2, 25), "February Travel Expense", [
            {"account": "5020", "debit": 14200.00, "desc": "Conference travel — increased this month", "cc_id": cc_sales.id},
            {"account": "2010", "credit": 14200.00},
        ])

        # March 2026
        make_je(date(2026, 3, 15), "March Product Revenue", [
            {"account": "1020", "debit": 210000.00},
            {"account": "4010", "credit": 210000.00, "pc_id": pc_product.id},
        ])
        make_je(date(2026, 3, 15), "March Service Revenue", [
            {"account": "1020", "debit": 63000.00},
            {"account": "4020", "credit": 63000.00, "pc_id": pc_services.id},
        ])
        make_je(date(2026, 3, 31), "March Salaries", [
            {"account": "5010", "debit": 87000.00, "cc_id": cc_ops.id},
            {"account": "2010", "credit": 87000.00},
        ])
        make_je(date(2026, 3, 31), "March Cloud Costs", [
            {"account": "5030", "debit": 13500.00, "cc_id": cc_ops.id},
            {"account": "2010", "credit": 13500.00},
        ])
        make_je(date(2026, 3, 20), "March Office Expense", [
            {"account": "5050", "debit": 4200.00, "cc_id": cc_admin.id},
            {"account": "2010", "credit": 4200.00},
        ])
        make_je(date(2026, 3, 31), "March Depreciation", [
            {"account": "5060", "debit": 3500.00},
            {"account": "1100", "credit": 3500.00},
        ])

        # Cash receipts (AR collections)
        make_je(date(2026, 1, 20), "Cash Collection January", [
            {"account": "1010", "debit": 130000.00},
            {"account": "1020", "credit": 130000.00},
        ])
        make_je(date(2026, 2, 22), "Cash Collection February", [
            {"account": "1010", "debit": 170000.00},
            {"account": "1020", "credit": 170000.00},
        ])
        make_je(date(2026, 3, 25), "Cash Collection March", [
            {"account": "1010", "debit": 220000.00},
            {"account": "1020", "credit": 220000.00},
        ])

        print(f"[OK] Seeded {je_counter - 1} journal entries with lines.")
        print("[OK] Sample data loaded successfully.")


if __name__ == "__main__":
    seed()
