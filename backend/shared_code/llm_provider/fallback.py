"""
Deterministic rule-based fallback when no LLM credentials are configured.
Handles common finance queries without hallucination risk.
"""
import re
from shared_code.llm_provider.base import BaseLLMProvider, LLMResponse, Message, ToolDefinition


class FallbackProvider(BaseLLMProvider):
    """
    Simple keyword-based intent detection that dispatches to finance tools.
    Used when Azure OpenAI is not configured.
    """

    @property
    def is_available(self) -> bool:
        return True  # Always available as a fallback

    def chat_completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        from shared_code.llm_provider.base import ToolCall

        user_msg = next(
            (m.content.lower() for m in reversed(messages) if m.role == "user"), ""
        )

        # Intent detection — map keywords to tool calls
        if any(k in user_msg for k in ["trial balance", "balance sheet"]):
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(tool_name="get_trial_balance", arguments={})],
                finish_reason="tool_calls",
            )
        elif any(k in user_msg for k in ["p&l", "pnl", "profit", "income statement"]):
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
        elif any(k in user_msg for k in ["balance of", "what is", "show me"]):
            # Extract account name after "balance of" or "show me"
            match = re.search(r"(?:balance of|show me|what is the)\s+(.+?)(?:\?|$)", user_msg)
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
        else:
            return LLMResponse(
                content=(
                    "I can answer finance questions such as: trial balance, P&L summary, "
                    "account balances, top expenses, and journal entries. "
                    "Please ask a specific finance question."
                ),
                tool_calls=[],
                finish_reason="stop",
            )
