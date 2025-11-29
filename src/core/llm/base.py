"""
Base LLM Interface

Abstract base class for LLM providers with unified interface.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional

logger = logging.getLogger(__name__)


class Role(Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class Message:
    """A message in a conversation."""
    role: Role
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API calls."""
        d = {"role": self.role.value, "content": self.content}
        if self.name:
            d["name"] = self.name
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str = "openai"
    model: str = "gpt-4-turbo-preview"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    timeout: int = 120
    max_retries: int = 3
    streaming: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str
    tool_calls: Optional[list[dict]] = None
    raw_response: Optional[dict] = None
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)
    
    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)


@dataclass
class StreamChunk:
    """A chunk from streaming response."""
    content: str
    finish_reason: Optional[str] = None
    tool_calls: Optional[list[dict]] = None


class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.
    
    Provides a unified interface for:
    - Chat completions
    - Streaming responses
    - Function/tool calling
    - Token counting
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.provider}")
        self._client: Any = None
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.
        
        Args:
            messages: Conversation history
            tools: Optional tool definitions for function calling
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with the generated content
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a completion for the given messages.
        
        Args:
            messages: Conversation history
            tools: Optional tool definitions
            **kwargs: Additional parameters
            
        Yields:
            StreamChunk objects with partial content
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass
    
    async def complete_with_retry(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Complete with automatic retry on failure."""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                return await self.complete(messages, tools, **kwargs)
            except Exception as e:
                last_error = e
                wait_time = 2 ** attempt
                self.logger.warning(
                    f"LLM call failed (attempt {attempt + 1}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
        
        raise last_error
    
    def build_system_prompt(
        self,
        base_prompt: str,
        context: Optional[dict] = None,
    ) -> str:
        """Build system prompt with optional context injection."""
        prompt = base_prompt
        
        if context:
            context_str = "\n\nContext:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            prompt += context_str
        
        return prompt
