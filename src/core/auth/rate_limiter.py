"""
Rate Limiter

Token bucket and sliding window rate limiting.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    by_ip: bool = True
    by_user: bool = True


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None


class TokenBucket:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # Tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now
            
            # Add tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    @property
    def remaining(self) -> int:
        """Get remaining tokens."""
        return int(self.tokens)


class SlidingWindow:
    """Sliding window rate limiter."""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size  # Seconds
        self.max_requests = max_requests
        self.requests: list[float] = []
        self._lock = asyncio.Lock()
    
    async def check(self) -> tuple[bool, int]:
        """Check if request is allowed."""
        async with self._lock:
            now = time.time()
            window_start = now - self.window_size
            
            # Remove old requests
            self.requests = [t for t in self.requests if t > window_start]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True, self.max_requests - len(self.requests)
            
            return False, 0
    
    def reset_time(self) -> float:
        """Get time until window resets."""
        if not self.requests:
            return 0
        return self.requests[0] + self.window_size - time.time()


class RateLimiter:
    """
    Composite rate limiter.
    
    Combines token bucket for burst handling and
    sliding window for sustained rate limiting.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Per-client rate limiters
        self._minute_windows: dict[str, SlidingWindow] = defaultdict(
            lambda: SlidingWindow(60, self.config.requests_per_minute)
        )
        self._hour_windows: dict[str, SlidingWindow] = defaultdict(
            lambda: SlidingWindow(3600, self.config.requests_per_hour)
        )
        self._burst_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                self.config.requests_per_minute / 60,
                self.config.burst_size,
            )
        )
    
    async def check(
        self,
        identifier: str,
        cost: int = 1,
    ) -> RateLimitResult:
        """
        Check if request is allowed.
        
        Args:
            identifier: Client identifier (IP, user ID, API key)
            cost: Request cost (for weighted limiting)
            
        Returns:
            RateLimitResult with status and metadata
        """
        # Check burst limit
        bucket = self._burst_buckets[identifier]
        if not await bucket.consume(cost):
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=1.0,  # Burst resets quickly
                retry_after=1.0,
            )
        
        # Check minute limit
        minute_window = self._minute_windows[identifier]
        minute_allowed, minute_remaining = await minute_window.check()
        
        if not minute_allowed:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=minute_window.reset_time(),
                retry_after=minute_window.reset_time(),
            )
        
        # Check hour limit
        hour_window = self._hour_windows[identifier]
        hour_allowed, hour_remaining = await hour_window.check()
        
        if not hour_allowed:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=hour_window.reset_time(),
                retry_after=hour_window.reset_time(),
            )
        
        return RateLimitResult(
            allowed=True,
            remaining=min(minute_remaining, hour_remaining),
            reset_time=min(minute_window.reset_time(), hour_window.reset_time()),
        )
    
    async def get_status(self, identifier: str) -> dict:
        """Get rate limit status for identifier."""
        bucket = self._burst_buckets[identifier]
        minute = self._minute_windows[identifier]
        hour = self._hour_windows[identifier]
        
        return {
            "identifier": identifier,
            "burst_remaining": bucket.remaining,
            "minute_remaining": self.config.requests_per_minute - len(minute.requests),
            "hour_remaining": self.config.requests_per_hour - len(hour.requests),
            "minute_reset": minute.reset_time(),
            "hour_reset": hour.reset_time(),
        }
    
    def reset(self, identifier: str) -> None:
        """Reset rate limits for identifier."""
        self._burst_buckets.pop(identifier, None)
        self._minute_windows.pop(identifier, None)
        self._hour_windows.pop(identifier, None)
