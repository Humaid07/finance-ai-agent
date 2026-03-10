"""
Azure Functions v2 app entry point.
Registers all HTTP routes and delegates to service functions.
Routes are kept thin — all business logic lives in shared_code/services/.
"""
import json
import logging
from datetime import date

import azure.functions as func

from shared_code.config import get_config
from shared_code.database import get_db_session
from shared_code.services.finance_service import FinanceService
from shared_code.services.ai_agent_service import AIAgentService

logger = logging.getLogger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_response(data, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(data, default=str),
        status_code=status_code,
        mimetype="application/json",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


def _error_response(message: str, status_code: int = 500) -> func.HttpResponse:
    return _json_response({"error": message}, status_code)


def _get_llm_provider():
    """Return the configured LLM provider or fallback."""
    config = get_config()
    if config.openai.is_configured:
        from shared_code.llm_provider.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider()
    else:
        logger.warning("Azure OpenAI not configured — using deterministic fallback.")
        from shared_code.llm_provider.fallback import FallbackProvider
        return FallbackProvider()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    try:
        with get_db_session() as session:
            session.execute(func.text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return _json_response({
        "status": "ok",
        "db": db_status,
        "environment": get_config().environment,
    })


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------

@app.route(route="hierarchy/tree", methods=["GET"])
def hierarchy_tree(req: func.HttpRequest) -> func.HttpResponse:
    """Return the full GL hierarchy as a nested tree."""
    try:
        with get_db_session() as session:
            service = FinanceService(session)
            tree = service.get_hierarchy_tree()
        return _json_response(tree)
    except Exception as e:
        logger.exception("hierarchy_tree error")
        return _error_response(str(e))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.route(route="reports/trial-balance", methods=["GET"])
def reports_trial_balance(req: func.HttpRequest) -> func.HttpResponse:
    """Trial balance report with optional date filters."""
    try:
        date_from_str = req.params.get("date_from")
        date_to_str = req.params.get("date_to")

        date_from = date.fromisoformat(date_from_str) if date_from_str else None
        date_to = date.fromisoformat(date_to_str) if date_to_str else None

        with get_db_session() as session:
            service = FinanceService(session)
            rows = service.get_trial_balance(date_from=date_from, date_to=date_to)

        return _json_response([vars(r) for r in rows])
    except Exception as e:
        logger.exception("trial_balance error")
        return _error_response(str(e))


@app.route(route="reports/pnl", methods=["GET"])
def reports_pnl(req: func.HttpRequest) -> func.HttpResponse:
    """Profit & Loss report."""
    try:
        date_from_str = req.params.get("date_from")
        date_to_str = req.params.get("date_to")

        date_from = date.fromisoformat(date_from_str) if date_from_str else None
        date_to = date.fromisoformat(date_to_str) if date_to_str else None

        with get_db_session() as session:
            service = FinanceService(session)
            result = service.get_pnl(date_from=date_from, date_to=date_to)

        return _json_response(vars(result))
    except Exception as e:
        logger.exception("pnl error")
        return _error_response(str(e))


@app.route(route="reports/dashboard", methods=["GET"])
def reports_dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """Dashboard KPI data."""
    try:
        with get_db_session() as session:
            service = FinanceService(session)
            data = service.get_dashboard()
        return _json_response(vars(data))
    except Exception as e:
        logger.exception("dashboard error")
        return _error_response(str(e))


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

@app.route(route="transactions/journal-lines", methods=["GET"])
def transactions_journal_lines(req: func.HttpRequest) -> func.HttpResponse:
    """Paginated journal lines with filters."""
    try:
        page = int(req.params.get("page", "1"))
        page_size = min(int(req.params.get("page_size", "50")), 200)
        date_from_str = req.params.get("date_from")
        date_to_str = req.params.get("date_to")
        account_id = req.params.get("account_id")

        date_from = date.fromisoformat(date_from_str) if date_from_str else None
        date_to = date.fromisoformat(date_to_str) if date_to_str else None

        with get_db_session() as session:
            service = FinanceService(session)
            result = service.get_journal_lines(
                date_from=date_from,
                date_to=date_to,
                account_id=account_id,
                page=page,
                page_size=page_size,
            )
        return _json_response(result)
    except Exception as e:
        logger.exception("journal_lines error")
        return _error_response(str(e))


@app.route(route="transactions/journal-entries", methods=["GET"])
def transactions_journal_entries(req: func.HttpRequest) -> func.HttpResponse:
    """Paginated journal entries."""
    try:
        page = int(req.params.get("page", "1"))
        page_size = min(int(req.params.get("page_size", "50")), 200)

        with get_db_session() as session:
            service = FinanceService(session)
            result = service.get_journal_entries(page=page, page_size=page_size)
        return _json_response(result)
    except Exception as e:
        logger.exception("journal_entries error")
        return _error_response(str(e))


# ---------------------------------------------------------------------------
# AI Chat
# ---------------------------------------------------------------------------

@app.route(route="ai/chat", methods=["POST"])
def ai_chat(req: func.HttpRequest) -> func.HttpResponse:
    """Finance AI agent chat endpoint."""
    try:
        body = req.get_json()
    except ValueError:
        return _error_response("Invalid JSON body", 400)

    question = body.get("question", "").strip()
    history = body.get("history", [])

    if not question:
        return _error_response("question is required", 400)

    try:
        llm_provider = _get_llm_provider()
        with get_db_session() as session:
            finance_service = FinanceService(session)
            agent = AIAgentService(llm_provider, finance_service)
            result = agent.chat(question, history)

        return _json_response(result)
    except Exception as e:
        logger.exception("ai_chat error")
        return _error_response(str(e))
