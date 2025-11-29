"""
LLM Provider Implementations

Concrete implementations for various LLM providers.
"""

import asyncio
import os
import logging
from typing import Any, AsyncIterator, Optional

from .base import BaseLLM, LLMConfig, LLMResponse, Message, StreamChunk, Role

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


class GeminiProvider(BaseLLM):
    """Google Gemini API provider (Gemini 3 Pro and other models)."""
    
    async def initialize(self) -> None:
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            api_key = self.config.api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable required")
            
            genai.configure(api_key=api_key)
            
            # Configure safety settings (Gemini best practice)
            self._safety_settings = [
                {
                    "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
                {
                    "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                },
            ]
            
            # Get model configuration
            self._model_name = self.config.model or "gemini-2.0-flash-exp"
            self._generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_output_tokens": self.config.max_tokens,
            }
            
            # Create generation config (grounding is handled per-request if needed)
            self._generation_config = {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_output_tokens": self.config.max_tokens,
            }
            
            self._client = genai.GenerativeModel(
                model_name=self._model_name,
                safety_settings=self._safety_settings,
            )
            
            self.logger.info(f"Gemini client initialized with model {self._model_name}")
        except ImportError:
            self.logger.warning("google-generativeai package not installed, using mock mode")
            self._client = None
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            self._client = None
    
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion using Gemini API."""
        if not self._client:
            return self._mock_response(messages)
        
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages(messages)
            
            # Prepare generation config
            from google.generativeai.types import GenerationConfig
            gen_config = GenerationConfig(
                temperature=kwargs.get("temperature", self.config.temperature),
                top_p=kwargs.get("top_p", self.config.top_p),
                max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            )
            
            # Convert tools to Gemini function calling format
            gemini_tools = None
            if tools:
                gemini_tools = self._convert_tools(tools)
            
            # Generate content
            response = await asyncio.to_thread(
                self._client.generate_content,
                gemini_messages,
                generation_config=gen_config,
                tools=gemini_tools,
            )
            
            # Extract content
            content = ""
            if hasattr(response, "text") and response.text:
                content = response.text
            
            # Extract tool calls
            tool_calls = None
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                        for part in candidate.content.parts:
                            if hasattr(part, "function_call"):
                                tool_calls = [{
                                    "id": f"call_{hash(str(part.function_call))}",
                                    "type": "function",
                                    "function": {
                                        "name": part.function_call.name,
                                        "arguments": str(part.function_call.args) if hasattr(part.function_call, "args") else "{}",
                                    },
                                }]
            
            # Extract usage information
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            if hasattr(response, "usage_metadata"):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }
            
            # Extract finish reason
            finish_reason = "stop"
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    finish_reason = str(candidate.finish_reason).lower() if candidate.finish_reason else "stop"
            
            return LLMResponse(
                content=content,
                model=self._model_name,
                usage=usage,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
                raw_response={
                    "candidates": len(response.candidates) if hasattr(response, "candidates") else 0,
                    "usage_metadata": usage,
                },
            )
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion from Gemini."""
        if not self._client:
            yield StreamChunk(content="Mock streaming response", finish_reason="stop")
            return
        
        try:
            gemini_messages = self._convert_messages(messages)
            
            gen_config = self._generation_config.copy()
            if kwargs.get("temperature") is not None:
                gen_config["temperature"] = kwargs["temperature"]
            if kwargs.get("max_tokens") is not None:
                gen_config["max_output_tokens"] = kwargs["max_tokens"]
            
            gemini_tools = None
            if tools:
                gemini_tools = self._convert_tools(tools)
            
            # Stream response
            response_stream = await asyncio.to_thread(
                self._client.generate_content,
                gemini_messages,
                generation_config=gen_config,
                tools=gemini_tools,
                stream=True,
            )
            
            async for chunk in response_stream:
                if chunk.text:
                    yield StreamChunk(content=chunk.text)
                if hasattr(chunk, "candidates") and chunk.candidates:
                    finish_reason = chunk.candidates[0].finish_reason.name.lower() if hasattr(chunk.candidates[0], "finish_reason") else None
                    if finish_reason:
                        yield StreamChunk(content="", finish_reason=finish_reason)
        except Exception as e:
            self.logger.error(f"Gemini streaming error: {e}")
            yield StreamChunk(content=f"Error: {e}", finish_reason="error")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's tokenizer."""
        if not self._client:
            # Rough estimate: Gemini uses similar tokenization to GPT
            return len(text) // 4
        
        try:
            # Use Gemini's count_tokens method
            result = self._client.count_tokens(text)
            if hasattr(result, "total_tokens"):
                return result.total_tokens
            return len(text) // 4
        except Exception:
            # Fallback estimate
            return len(text) // 4
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert messages to Gemini format."""
        gemini_messages = []
        
        for msg in messages:
            if msg.role == Role.SYSTEM:
                # Gemini doesn't have system messages, prepend to first user message
                if gemini_messages and gemini_messages[0].get("role") == "user":
                    gemini_messages[0]["parts"] = [f"System: {msg.content}\n\nUser: {gemini_messages[0]['parts'][0]}"]
                else:
                    # Store system message to prepend later
                    gemini_messages.append({"role": "user", "parts": [f"System: {msg.content}"]})
            elif msg.role == Role.USER:
                gemini_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role == Role.ASSISTANT:
                gemini_messages.append({"role": "model", "parts": [msg.content]})
        
        return gemini_messages
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool format to Gemini function calling format."""
        gemini_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                gemini_tools.append({
                    "function_declarations": [{
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    }]
                })
        
        return gemini_tools if gemini_tools else None
    
    def _mock_response(self, messages: list[Message]) -> LLMResponse:
        """Generate mock response."""
        return LLMResponse(
            content=f"Mock Gemini response for: {messages[-1].content[:50]}...",
            model=self._model_name if hasattr(self, "_model_name") else "gemini-2.0-flash-exp",
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
        "gemini": GeminiProvider,
        "google": GeminiProvider,
    }
    
    provider_class = providers.get(config.provider.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {config.provider}. Available: {list(providers.keys())}")
    
    return provider_class(config)
