"""
Finance AI Agent service.
Orchestrates tool-based reasoning: LLM → tool call → tool result → LLM → answer.
"""
import logging
from datetime import date
from typing import Any

from shared_code.llm_provider.base import BaseLLMProvider, Message, ToolDefinition
from shared_code.prompt_templates.finance_agent import (
    FINANCE_AGENT_SYSTEM_PROMPT,
    build_user_message,
    build_tool_result_message,
)
from shared_code.services.finance_service import FinanceService

logger = logging.getLogger(__name__)

# Tool definitions exposed to the LLM
FINANCE_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_trial_balance",
        description="Returns the trial balance with debit, credit, and net balance for all GL accounts.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD (optional)"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_account_balance",
        description="Returns the balance for a specific GL account by name or code.",
        parameters={
            "type": "object",
            "properties": {
                "account_name": {"type": "string", "description": "Account name or code to look up"},
            },
            "required": ["account_name"],
        },
    ),
    ToolDefinition(
        name="get_pnl",
        description="Returns the Profit & Loss statement with revenue, expenses, and net income.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD (optional)"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_top_expenses",
        description="Returns the top expense accounts ranked by total amount.",
        parameters={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of results (default 5)"},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_journal_lines",
        description="Returns journal transaction lines with optional date and account filters.",
        parameters={
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "description": "Start date YYYY-MM-DD (optional)"},
                "date_to": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
                "account_id": {"type": "string", "description": "Filter by account UUID (optional)"},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="explain_variance",
        description="Compares an account's balance across two periods and explains the variance.",
        parameters={
            "type": "object",
            "properties": {
                "account_name": {"type": "string", "description": "Account name to analyze"},
                "period_1": {"type": "string", "description": "First period YYYY-MM"},
                "period_2": {"type": "string", "description": "Second period YYYY-MM"},
            },
            "required": ["account_name", "period_1", "period_2"],
        },
    ),
]


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


class AIAgentService:
    def __init__(self, llm_provider: BaseLLMProvider, finance_service: FinanceService):
        self.llm = llm_provider
        self.finance = finance_service

    def _execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """Dispatch LLM tool call to the appropriate finance service method."""
        logger.info(f"Executing finance tool: {tool_name} args={arguments}")

        if tool_name == "get_trial_balance":
            result = self.finance.get_trial_balance(
                date_from=_parse_date(arguments.get("date_from")),
                date_to=_parse_date(arguments.get("date_to")),
            )
            return [vars(r) for r in result]

        elif tool_name == "get_account_balance":
            return self.finance.get_account_balance(arguments["account_name"])

        elif tool_name == "get_pnl":
            result = self.finance.get_pnl(
                date_from=_parse_date(arguments.get("date_from")),
                date_to=_parse_date(arguments.get("date_to")),
            )
            return vars(result)

        elif tool_name == "get_top_expenses":
            limit = arguments.get("limit", 5)
            return self.finance.get_top_expenses(limit)

        elif tool_name == "get_journal_lines":
            result = self.finance.get_journal_lines(
                date_from=_parse_date(arguments.get("date_from")),
                date_to=_parse_date(arguments.get("date_to")),
                account_id=arguments.get("account_id"),
            )
            return result

        elif tool_name == "explain_variance":
            return self.finance.explain_variance(
                account_name=arguments["account_name"],
                period_1=arguments["period_1"],
                period_2=arguments["period_2"],
            )

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def chat(self, question: str, conversation_history: list[dict] | None = None) -> dict:
        """
        Process a finance question through the agent loop.
        Returns answer text and evidence data from tool calls.
        """
        messages = [Message(role="system", content=FINANCE_AGENT_SYSTEM_PROMPT)]

        # Include prior conversation turns if provided
        if conversation_history:
            for turn in conversation_history[-6:]:  # Keep last 3 exchanges
                messages.append(Message(role=turn["role"], content=turn["content"]))

        messages.append(Message(role="user", content=build_user_message(question)))

        evidence = []
        max_iterations = 3  # Safety limit on agentic loops

        for iteration in range(max_iterations):
            response = self.llm.chat_completion(
                messages=messages,
                tools=FINANCE_TOOLS,
            )

            if response.finish_reason == "error":
                return {
                    "answer": "I encountered an error processing your request. Please try again.",
                    "evidence": [],
                }

            # No tool calls — we have a final answer
            if not response.tool_calls:
                return {
                    "answer": response.content or "No answer generated.",
                    "evidence": evidence,
                }

            # Execute all tool calls and collect evidence
            for tool_call in response.tool_calls:
                tool_result = self._execute_tool(
                    tool_call.tool_name, tool_call.arguments
                )
                evidence.append({
                    "tool": tool_call.tool_name,
                    "arguments": tool_call.arguments,
                    "result": tool_result,
                })

                # Feed tool result back into conversation
                result_message = build_tool_result_message(tool_call.tool_name, tool_result)
                messages.append(Message(role="user", content=result_message))

        # Fallback if max iterations reached without a final answer
        return {
            "answer": "I gathered the following data from your finance system.",
            "evidence": evidence,
        }
