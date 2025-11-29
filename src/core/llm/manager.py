"""
LLM Manager

Manages multiple LLM providers with load balancing, fallback, and caching.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from .base import BaseLLM, LLMConfig, LLMResponse, Message
from .providers import get_provider

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry for LLM responses."""
    response: LLMResponse
    timestamp: float
    hits: int = 0


@dataclass
class ProviderStats:
    """Statistics for an LLM provider."""
    requests: int = 0
    failures: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None


class LLMManager:
    """
    Manager for LLM providers with advanced features.
    
    Features:
    - Multiple provider support with fallback
    - Response caching
    - Rate limiting
    - Usage tracking
    - Load balancing
    """
    
    def __init__(
        self,
        primary_config: LLMConfig,
        fallback_configs: Optional[list[LLMConfig]] = None,
        cache_ttl: int = 3600,
        cache_max_size: int = 1000,
    ):
        self.primary_config = primary_config
        self.fallback_configs = fallback_configs or []
        self.cache_ttl = cache_ttl
        self.cache_max_size = cache_max_size
        
        self._providers: list[BaseLLM] = []
        self._cache: dict[str, CacheEntry] = {}
        self._stats: dict[str, ProviderStats] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all providers."""
        if self._initialized:
            return
        
        # Initialize primary provider
        primary = get_provider(self.primary_config)
        await primary.initialize()
        self._providers.append(primary)
        self._stats[self.primary_config.provider] = ProviderStats()
        
        # Initialize fallback providers
        for config in self.fallback_configs:
            provider = get_provider(config)
            await provider.initialize()
            self._providers.append(provider)
            self._stats[config.provider] = ProviderStats()
        
        self._initialized = True
        logger.info(f"LLMManager initialized with {len(self._providers)} providers")
    
    async def complete(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate completion with automatic fallback.
        
        Args:
            messages: Conversation messages
            tools: Optional tool definitions
            use_cache: Whether to use response cache
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse from successful provider
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache
        if use_cache and not tools:  # Don't cache tool calls
            cache_key = self._cache_key(messages)
            cached = self._get_cached(cache_key)
            if cached:
                logger.debug("Returning cached response")
                return cached
        
        # Try providers in order
        last_error = None
        for provider in self._providers:
            try:
                start_time = time.time()
                response = await provider.complete(messages, tools, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Update stats
                stats = self._stats[provider.config.provider]
                stats.requests += 1
                stats.total_tokens += response.total_tokens
                stats.total_latency_ms += latency
                
                # Cache response
                if use_cache and not tools:
                    self._set_cached(cache_key, response)
                
                return response
                
            except Exception as e:
                logger.warning(f"Provider {provider.config.provider} failed: {e}")
                last_error = e
                
                # Update error stats
                stats = self._stats[provider.config.provider]
                stats.failures += 1
                stats.last_error = str(e)
                stats.last_error_time = time.time()
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    async def complete_with_context(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[dict] = None,
        history: Optional[list[Message]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Convenience method for common completion pattern.
        
        Args:
            system_prompt: System instructions
            user_message: User's message
            context: Optional context to inject
            history: Optional conversation history
            **kwargs: Additional parameters
        """
        messages = []
        
        # Build system message with context
        if context:
            system_prompt = self._inject_context(system_prompt, context)
        messages.append(Message(role="system", content=system_prompt))
        
        # Add history
        if history:
            messages.extend(history)
        
        # Add user message
        messages.append(Message(role="user", content=user_message))
        
        return await self.complete(messages, **kwargs)
    
    def _cache_key(self, messages: list[Message]) -> str:
        """Generate cache key from messages."""
        content = json.dumps([m.to_dict() for m in messages], sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[LLMResponse]:
        """Get cached response if valid."""
        entry = self._cache.get(key)
        if not entry:
            return None
        
        if time.time() - entry.timestamp > self.cache_ttl:
            del self._cache[key]
            return None
        
        entry.hits += 1
        return entry.response
    
    def _set_cached(self, key: str, response: LLMResponse) -> None:
        """Cache a response."""
        # Evict old entries if cache is full
        if len(self._cache) >= self.cache_max_size:
            # Remove oldest entries
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].timestamp,
            )
            for old_key in sorted_keys[:100]:  # Remove 100 oldest
                del self._cache[old_key]
        
        self._cache[key] = CacheEntry(
            response=response,
            timestamp=time.time(),
        )
    
    def _inject_context(self, prompt: str, context: dict) -> str:
        """Inject context into system prompt."""
        context_section = "\n\n## Current Context\n"
        for key, value in context.items():
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)
            context_section += f"### {key}\n{value}\n\n"
        return prompt + context_section
    
    def get_stats(self) -> dict[str, Any]:
        """Get manager statistics."""
        stats = {
            "providers": {},
            "cache": {
                "size": len(self._cache),
                "max_size": self.cache_max_size,
                "ttl_seconds": self.cache_ttl,
            },
        }
        
        for provider, pstats in self._stats.items():
            avg_latency = 0
            if pstats.requests > 0:
                avg_latency = pstats.total_latency_ms / pstats.requests
            
            stats["providers"][provider] = {
                "requests": pstats.requests,
                "failures": pstats.failures,
                "success_rate": 1 - (pstats.failures / max(pstats.requests, 1)),
                "total_tokens": pstats.total_tokens,
                "avg_latency_ms": round(avg_latency, 2),
                "last_error": pstats.last_error,
            }
        
        return stats
    
    async def clear_cache(self) -> int:
        """Clear the response cache."""
        count = len(self._cache)
        self._cache.clear()
        return count
