"""
Deterministic rule-based fallback when no LLM credentials are configured.
Handles common finance queries without hallucination risk.

On the first call: detects intent and returns a tool call.
On the second call (tool result in messages): formats a readable answer from the data.
"""
import json
import re
from shared_code.llm_provider.base import BaseLLMProvider, LLMResponse, Message, ToolDefinition


class FallbackProvider(BaseLLMProvider):
    """
    Two-phase fallback:
    1. Detect intent → issue tool call
    2. Tool result injected → format natural language answer
    """

    @property
    def is_available(self) -> bool:
        return True

    def chat_completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        from shared_code.llm_provider.base import ToolCall

        # Check if the latest user message is a tool result (second phase)
        last_user = next(
            (m for m in reversed(messages) if m.role == "user"), None
        )
        if last_user and last_user.content.startswith("Tool '"):
            return self._format_tool_result(last_user.content)

        # First phase: find the original question
        user_msg = last_user.content.lower() if last_user else ""

        if any(k in user_msg for k in ["trial balance", "balance sheet"]):
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(tool_name="get_trial_balance", arguments={})],
                finish_reason="tool_calls",
            )
        elif any(k in user_msg for k in ["p&l", "pnl", "profit", "income statement", "revenue"]):
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(tool_name="get_pnl", arguments={})],
                finish_reason="tool_calls",
            )
        elif any(k in user_msg for k in ["top expense", "highest expense", "biggest expense"]):
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(tool_name="get_top_expenses", arguments={"limit": 5})],
                finish_reason="tool_calls",
            )
        elif any(k in user_msg for k in ["balance of", "balance", "what is", "show me", "cash"]):
            match = re.search(r"(?:balance of|show me|what is the|balance)\s+(.+?)(?:\?|$)", user_msg)
            account_name = match.group(1).strip() if match else "cash"
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        tool_name="get_account_balance",
                        arguments={"account_name": account_name},
                    )
                ],
                finish_reason="tool_calls",
            )
        elif any(k in user_msg for k in ["journal", "transaction", "posting"]):
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(tool_name="get_journal_lines", arguments={})],
                finish_reason="tool_calls",
            )
        elif any(k in user_msg for k in ["dashboard", "summary", "overview", "kpi"]):
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(tool_name="get_pnl", arguments={})],
                finish_reason="tool_calls",
            )
        else:
            return LLMResponse(
                content=(
                    "I can answer finance questions such as:\n"
                    "- Trial balance\n- P&L summary\n- Account balances (e.g. 'cash balance')\n"
                    "- Top expenses\n- Journal entries\n\nPlease ask a specific finance question."
                ),
                tool_calls=[],
                finish_reason="stop",
            )

    def _format_tool_result(self, tool_message: str) -> LLMResponse:
        """Parse the tool result message and generate a readable answer."""
        try:
            # Extract tool name
            tool_match = re.match(r"Tool '(\w+)' returned:", tool_message)
            tool_name = tool_match.group(1) if tool_match else "unknown"

            # Extract JSON result
            json_str = tool_message[tool_message.index("\n") + 1:]
            data = json.loads(json_str)

            answer = self._narrate(tool_name, data)
        except Exception:
            answer = "Here is the data retrieved from your finance system."

        return LLMResponse(content=answer, tool_calls=[], finish_reason="stop")

    def _narrate(self, tool_name: str, data) -> str:
        """Convert structured finance data into a plain English summary."""
        def fmt(n):
            try:
                return "${:,.2f}".format(float(n))
            except Exception:
                return str(n)

        if tool_name == "get_pnl" and isinstance(data, dict):
            rev = fmt(data.get("revenue", 0))
            exp = fmt(data.get("expenses", 0))
            net = fmt(data.get("net_income", 0))
            direction = "profitable" if float(data.get("net_income", 0)) >= 0 else "at a loss"
            return (
                f"Here is your Profit & Loss summary:\n\n"
                f"- Total Revenue: {rev}\n"
                f"- Total Expenses: {exp}\n"
                f"- Net Income: {net}\n\n"
                f"The company is currently {direction}."
            )

        elif tool_name == "get_trial_balance" and isinstance(data, list):
            lines = [f"- {r['account_code']} {r['account_name']}: {fmt(r['balance'])}" for r in data[:10]]
            suffix = f"\n  ...and {len(data) - 10} more accounts." if len(data) > 10 else ""
            return "Trial Balance (top accounts by code):\n\n" + "\n".join(lines) + suffix

        elif tool_name == "get_top_expenses" and isinstance(data, list):
            lines = [f"{i+1}. {r['account_name']}: {fmt(r['balance'])}" for i, r in enumerate(data)]
            return "Top Expense Accounts:\n\n" + "\n".join(lines)

        elif tool_name == "get_account_balance" and isinstance(data, dict):
            if not data.get("found"):
                return f"No account found matching '{data.get('account', 'that name')}'."
            return (
                f"Account: {data['account_name']} ({data['account_code']})\n"
                f"Type: {data['account_type']}\n"
                f"Balance: {fmt(data['balance'])}\n"
                f"  Debit Total:  {fmt(data['debit'])}\n"
                f"  Credit Total: {fmt(data['credit'])}"
            )

        elif tool_name == "get_journal_lines" and isinstance(data, dict):
            total = data.get("total", 0)
            items = data.get("items", [])[:5]
            lines = [
                f"- {r['posting_date']} | {r.get('account_name','?')} | "
                f"Dr: {fmt(r['debit'])} Cr: {fmt(r['credit'])}"
                for r in items
            ]
            return f"Journal Lines ({total} total, showing first {len(lines)}):\n\n" + "\n".join(lines)

        elif tool_name == "explain_variance" and isinstance(data, dict):
            return (
                f"Variance Analysis for {data.get('account')}:\n\n"
                f"- {data.get('period_1')}: {fmt(data.get('period_1_balance', 0))}\n"
                f"- {data.get('period_2')}: {fmt(data.get('period_2_balance', 0))}\n"
                f"- Variance: {fmt(data.get('variance', 0))} ({data.get('variance_pct', 0)}%)"
            )

        return "Data retrieved successfully from your finance system."
