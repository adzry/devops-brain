"""
LLM Provider Implementations

Concrete implementations for various LLM providers.
"""

import os
import logging
from typing import Any, AsyncIterator, Optional

from .base import BaseLLM, LLMConfig, LLMResponse, Message, StreamChunk

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLM):
    """OpenAI API provider (GPT-4, GPT-3.5, etc.)."""
    
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI
            
            api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout,
            )
            self.logger.info(f"OpenAI client initialized with model {self.config.model}")
        except ImportError:
            self.logger.warning("OpenAI package not installed, using mock mode")
            self._client = None
    
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        if not self._client:
            return self._mock_response(messages)
        
        params = {
            "model": kwargs.get("model", self.config.model),
            "messages": [m.to_dict() for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        response = await self._client.chat.completions.create(**params)
        
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason,
            tool_calls=[tc.model_dump() for tc in choice.message.tool_calls] if choice.message.tool_calls else None,
            raw_response=response.model_dump(),
        )
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from OpenAI."""
        if not self._client:
            yield StreamChunk(content="Mock streaming response", finish_reason="stop")
            return
        
        params = {
            "model": kwargs.get("model", self.config.model),
            "messages": [m.to_dict() for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }
        
        if tools:
            params["tools"] = tools
        
        stream = await self._client.chat.completions.create(**params)
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield StreamChunk(
                    content=chunk.choices[0].delta.content,
                    finish_reason=chunk.choices[0].finish_reason,
                )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.config.model)
            return len(encoding.encode(text))
        except Exception:
            # Rough estimate: ~4 chars per token
            return len(text) // 4
    
    def _mock_response(self, messages: list[Message]) -> LLMResponse:
        """Generate mock response for testing."""
        return LLMResponse(
            content=f"Mock response for: {messages[-1].content[:50]}...",
            model=self.config.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
        )


class AnthropicProvider(BaseLLM):
    """Anthropic API provider (Claude models)."""
    
    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic
            
            api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            self._client = AsyncAnthropic(api_key=api_key)
            self.logger.info(f"Anthropic client initialized with model {self.config.model}")
        except ImportError:
            self.logger.warning("Anthropic package not installed, using mock mode")
            self._client = None
    
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Anthropic API."""
        if not self._client:
            return self._mock_response(messages)
        
        # Extract system message
        system_content = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                chat_messages.append({
                    "role": "user" if msg.role.value == "user" else "assistant",
                    "content": msg.content,
                })
        
        params = {
            "model": kwargs.get("model", self.config.model),
            "messages": chat_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
        }
        
        if system_content:
            params["system"] = system_content
        
        if tools:
            params["tools"] = self._convert_tools(tools)
        
        response = await self._client.messages.create(**params)
        
        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {"name": block.name, "arguments": str(block.input)},
                })
        
        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason or "stop",
            tool_calls=tool_calls if tool_calls else None,
        )
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from Anthropic."""
        if not self._client:
            yield StreamChunk(content="Mock streaming response", finish_reason="stop")
            return
        
        # Similar setup as complete
        system_content = ""
        chat_messages = []
        for msg in messages:
            if msg.role.value == "system":
                system_content = msg.content
            else:
                chat_messages.append({
                    "role": "user" if msg.role.value == "user" else "assistant",
                    "content": msg.content,
                })
        
        params = {
            "model": kwargs.get("model", self.config.model),
            "messages": chat_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }
        
        if system_content:
            params["system"] = system_content
        
        async with self._client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield StreamChunk(content=text)
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for Claude."""
        # Claude uses roughly similar tokenization to GPT
        return len(text) // 4
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool format to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })
        return anthropic_tools
    
    def _mock_response(self, messages: list[Message]) -> LLMResponse:
        """Generate mock response."""
        return LLMResponse(
            content=f"Mock Claude response for: {messages[-1].content[:50]}...",
            model=self.config.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="end_turn",
        )


def get_provider(config: LLMConfig) -> BaseLLM:
    """Factory function to get the appropriate LLM provider."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,
    }
    
    provider_class = providers.get(config.provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {config.provider}")
    
    return provider_class(config)
