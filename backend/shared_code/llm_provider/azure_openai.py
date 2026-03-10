"""
Azure OpenAI LLM provider implementation.
Reads credentials from environment variables via config module.
Supports tool/function calling for agent workflows.
"""
import json
import logging

from shared_code.llm_provider.base import (
    BaseLLMProvider,
    LLMResponse,
    Message,
    ToolCall,
    ToolDefinition,
)
from shared_code.config import get_config

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI implementation using the openai SDK."""

    def __init__(self):
        self._client = None
        self._config = get_config().openai

    def _get_client(self):
        """Lazy initialize the Azure OpenAI client."""
        if self._client is None:
            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    azure_endpoint=self._config.endpoint,
                    api_key=self._config.api_key,
                    api_version=self._config.api_version,
                )
            except ImportError:
                logger.error("openai package not installed. Run: pip install openai")
                raise
        return self._client

    @property
    def is_available(self) -> bool:
        return self._config.is_configured

    def chat_completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        if not self.is_available:
            raise RuntimeError("Azure OpenAI is not configured")

        client = self._get_client()
        openai_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        kwargs = {
            "model": self._config.deployment,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            kwargs["tool_choice"] = "auto"

        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            tool_calls = []

            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            tool_name=tc.function.name,
                            arguments=json.loads(tc.function.arguments),
                        )
                    )

            return LLMResponse(
                content=choice.message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error(f"Azure OpenAI call failed: {e}")
            return LLMResponse(
                content=None,
                tool_calls=[],
                finish_reason="error",
            )
