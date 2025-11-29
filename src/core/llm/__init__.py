"""
LLM Integration Layer

Provides a unified interface for interacting with various LLM providers.
"""

from .base import BaseLLM, LLMConfig, LLMResponse, Message, Role
from .providers import OpenAIProvider, AnthropicProvider, get_provider
from .manager import LLMManager

__all__ = [
    "BaseLLM",
    "LLMConfig", 
    "LLMResponse",
    "Message",
    "Role",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_provider",
    "LLMManager",
]
