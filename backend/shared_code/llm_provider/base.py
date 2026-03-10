"""
Abstract LLM provider interface.
All LLM implementations must extend BaseLLMProvider.
This decouples business logic from specific LLM vendors.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema


@dataclass
class ToolCall:
    tool_name: str
    arguments: dict


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall]
    finish_reason: str  # "stop", "tool_calls", "error"


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def chat_completion(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Send chat messages and return response, optionally with tool calls."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is properly configured and ready."""
        ...
