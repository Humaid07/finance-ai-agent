"""
Local development server using FastAPI + Uvicorn.
Serves the same routes as the Azure Functions app without needing the func CLI.
Run: python dev_server.py
"""
import os
import sys
from datetime import date
from contextlib import asynccontextmanager

# Load local.settings.json env vars before importing anything else
import json

settings_file = os.path.join(os.path.dirname(__file__), "local.settings.json")
if os.path.exists(settings_file):
    with open(settings_file) as f:
        settings = json.load(f)
    for k, v in settings.get("Values", {}).items():
        os.environ.setdefault(k, v)
    print(f"Loaded settings from {settings_file}")

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared_code.config import get_config
from shared_code.database import get_db_session
from shared_code.services.finance_service import FinanceService
from shared_code.services.ai_agent_service import AIAgentService


app = FastAPI(title="Finance AI Agent — Dev Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_llm_provider():
    config = get_config()
    if config.openai.is_configured:
        from shared_code.llm_provider.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider()
    from shared_code.llm_provider.fallback import FallbackProvider
    return FallbackProvider()


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    try:
        with get_db_session() as session:
            session.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return {"status": "ok", "db": db_status, "environment": get_config().environment}


# ── Hierarchy ─────────────────────────────────────────────────────────────

@app.get("/api/hierarchy/tree")
def hierarchy_tree():
    with get_db_session() as session:
        svc = FinanceService(session)
        return svc.get_hierarchy_tree()


# ── Reports ───────────────────────────────────────────────────────────────

@app.get("/api/reports/trial-balance")
def trial_balance(date_from: str | None = None, date_to: str | None = None):
    df = date.fromisoformat(date_from) if date_from else None
    dt = date.fromisoformat(date_to) if date_to else None
    with get_db_session() as session:
        svc = FinanceService(session)
        rows = svc.get_trial_balance(df, dt)
    return [vars(r) for r in rows]


@app.get("/api/reports/pnl")
def pnl(date_from: str | None = None, date_to: str | None = None):
    df = date.fromisoformat(date_from) if date_from else None
    dt = date.fromisoformat(date_to) if date_to else None
    with get_db_session() as session:
        svc = FinanceService(session)
        result = svc.get_pnl(df, dt)
    return vars(result)


@app.get("/api/reports/dashboard")
def dashboard():
    with get_db_session() as session:
        svc = FinanceService(session)
        data = svc.get_dashboard()
    return vars(data)


# ── Transactions ──────────────────────────────────────────────────────────

@app.get("/api/transactions/journal-lines")
def journal_lines(
    page: int = 1,
    page_size: int = 50,
    date_from: str | None = None,
    date_to: str | None = None,
    account_id: str | None = None,
):
    df = date.fromisoformat(date_from) if date_from else None
    dt = date.fromisoformat(date_to) if date_to else None
    page_size = min(page_size, 200)
    with get_db_session() as session:
        svc = FinanceService(session)
        return svc.get_journal_lines(df, dt, account_id, page, page_size)


@app.get("/api/transactions/journal-entries")
def journal_entries(page: int = 1, page_size: int = 50):
    page_size = min(page_size, 200)
    with get_db_session() as session:
        svc = FinanceService(session)
        return svc.get_journal_entries(page, page_size)


# ── AI Chat ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/api/ai/chat")
def ai_chat(body: ChatRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    llm = get_llm_provider()
    with get_db_session() as session:
        finance_svc = FinanceService(session)
        agent = AIAgentService(llm, finance_svc)
        result = agent.chat(body.question, body.history)
    return result


if __name__ == "__main__":
    import uvicorn
    print("\n Finance AI Agent — Dev Server")
    print(" API:  http://localhost:7071/api")
    print(" Docs: http://localhost:7071/docs\n")
    uvicorn.run("dev_server:app", host="0.0.0.0", port=7071, reload=True)
