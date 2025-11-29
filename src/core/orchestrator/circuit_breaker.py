"""
Circuit Breaker Pattern

Prevents cascade failures by stopping requests to failing services.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Open after N failures
    success_threshold: int = 2  # Close after N successes in half-open
    timeout_seconds: int = 60  # Time before trying half-open
    failure_window_seconds: int = 60  # Window for counting failures


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    state: CircuitState
    failures: int = 0
    successes: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    total_requests: int = 0
    rejected_requests: int = 0


class CircuitBreaker:
    """
    Circuit breaker for preventing cascade failures.
    
    Features:
    - Automatic state transitions
    - Configurable thresholds
    - Failure window tracking
    - Statistics tracking
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats(state=self._state)
        self._failure_times: list[datetime] = []
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        async with self._lock:
            # Check if circuit is open
            if self._state == CircuitState.OPEN:
                # Check if timeout has passed
                if self._stats.opened_at:
                    elapsed = (datetime.utcnow() - self._stats.opened_at).total_seconds()
                    if elapsed >= self.config.timeout_seconds:
                        # Transition to half-open
                        self._state = CircuitState.HALF_OPEN
                        self._stats.successes = 0
                        self.logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
                    else:
                        # Still open, reject request
                        self._stats.rejected_requests += 1
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker {self.name} is OPEN. "
                            f"Retry after {self.config.timeout_seconds - int(elapsed)}s"
                        )
            
            self._stats.total_requests += 1
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
            
        except Exception as e:
            await self._record_failure()
            raise
    
    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self._stats.last_success = datetime.utcnow()
            
            if self._state == CircuitState.HALF_OPEN:
                self._stats.successes += 1
                if self._stats.successes >= self.config.success_threshold:
                    # Transition to closed
                    self._state = CircuitState.CLOSED
                    self._stats.state = CircuitState.CLOSED
                    self._failure_times.clear()
                    self._stats.failures = 0
                    self.logger.info(f"Circuit {self.name} CLOSED after recovery")
            
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_times.clear()
                self._stats.failures = 0
    
    async def _record_failure(self) -> None:
        """Record a failed call."""
        async with self._lock:
            now = datetime.utcnow()
            self._stats.last_failure = now
            self._failure_times.append(now)
            
            # Clean old failures outside window
            window_start = now - timedelta(seconds=self.config.failure_window_seconds)
            self._failure_times = [
                ft for ft in self._failure_times
                if ft >= window_start
            ]
            
            self._stats.failures = len(self._failure_times)
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._state = CircuitState.OPEN
                self._stats.state = CircuitState.OPEN
                self._stats.opened_at = now
                self._stats.successes = 0
                self.logger.warning(f"Circuit {self.name} OPENED after failure in HALF_OPEN")
            
            elif self._state == CircuitState.CLOSED:
                if self._stats.failures >= self.config.failure_threshold:
                    # Open the circuit
                    self._state = CircuitState.OPEN
                    self._stats.state = CircuitState.OPEN
                    self._stats.opened_at = now
                    self.logger.error(
                        f"Circuit {self.name} OPENED after {self._stats.failures} failures"
                    )
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failures": self._stats.failures,
            "successes": self._stats.successes,
            "total_requests": self._stats.total_requests,
            "rejected_requests": self._stats.rejected_requests,
            "last_failure": self._stats.last_failure.isoformat() if self._stats.last_failure else None,
            "last_success": self._stats.last_success.isoformat() if self._stats.last_success else None,
            "opened_at": self._stats.opened_at.isoformat() if self._stats.opened_at else None,
        }
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._stats.state = CircuitState.CLOSED
        self._stats.failures = 0
        self._stats.successes = 0
        self._failure_times.clear()
        self._stats.opened_at = None
        self.logger.info(f"Circuit {self.name} manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    def get_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
    
    def list_breakers(self) -> list[dict]:
        """List all circuit breakers and their stats."""
        return [breaker.get_stats() for breaker in self._breakers.values()]
    
    def reset_breaker(self, name: str) -> bool:
        """Reset a circuit breaker."""
        breaker = self._breakers.get(name)
        if breaker:
            breaker.reset()
            return True
        return False
