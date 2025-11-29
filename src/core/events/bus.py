"""
Event Bus

Central event bus for pub/sub communication.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Coroutine, Optional
from weakref import WeakSet

from .types import Event, EventType

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


@dataclass
class Subscription:
    """Event subscription."""
    handler: EventHandler
    event_types: set[EventType]
    filter_fn: Optional[Callable[[Event], bool]] = None
    once: bool = False


class EventBus:
    """
    Central event bus for pub/sub communication.
    
    Features:
    - Async event handling
    - Pattern-based subscriptions
    - Event filtering
    - Event history
    - Dead letter queue
    """
    
    _instance: Optional["EventBus"] = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._subscribers: dict[EventType, list[Subscription]] = defaultdict(list)
        self._all_subscribers: list[Subscription] = []
        self._history: list[Event] = []
        self._dead_letters: list[tuple[Event, str]] = []
        self._history_max_size = 1000
        self._lock = asyncio.Lock()
        self._processing = False
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._initialized = True
        
        logger.info("EventBus initialized")
    
    async def start(self) -> None:
        """Start the event processing loop."""
        self._processing = True
        asyncio.create_task(self._process_events())
        logger.info("EventBus started")
    
    async def stop(self) -> None:
        """Stop the event bus."""
        self._processing = False
        logger.info("EventBus stopped")
    
    def subscribe(
        self,
        event_types: EventType | list[EventType],
        handler: EventHandler,
        filter_fn: Optional[Callable[[Event], bool]] = None,
        once: bool = False,
    ) -> Subscription:
        """
        Subscribe to events.
        
        Args:
            event_types: Event type(s) to subscribe to
            handler: Async handler function
            filter_fn: Optional filter function
            once: If True, unsubscribe after first event
            
        Returns:
            Subscription object
        """
        if isinstance(event_types, EventType):
            event_types = [event_types]
        
        subscription = Subscription(
            handler=handler,
            event_types=set(event_types),
            filter_fn=filter_fn,
            once=once,
        )
        
        for event_type in event_types:
            self._subscribers[event_type].append(subscription)
        
        logger.debug(f"New subscription for {[e.value for e in event_types]}")
        return subscription
    
    def subscribe_all(
        self,
        handler: EventHandler,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> Subscription:
        """Subscribe to all events."""
        subscription = Subscription(
            handler=handler,
            event_types=set(),
            filter_fn=filter_fn,
        )
        self._all_subscribers.append(subscription)
        return subscription
    
    def unsubscribe(self, subscription: Subscription) -> None:
        """Unsubscribe from events."""
        for event_type in subscription.event_types:
            if subscription in self._subscribers[event_type]:
                self._subscribers[event_type].remove(subscription)
        
        if subscription in self._all_subscribers:
            self._all_subscribers.remove(subscription)
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event.
        
        Args:
            event: Event to publish
        """
        await self._queue.put(event)
        
        # Add to history
        self._history.append(event)
        if len(self._history) > self._history_max_size:
            self._history = self._history[-self._history_max_size:]
        
        logger.debug(f"Event published: {event.type.value}")
    
    async def publish_sync(self, event: Event) -> None:
        """Publish and process event synchronously."""
        await self._dispatch(event)
    
    async def _process_events(self) -> None:
        """Background event processing loop."""
        while self._processing:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                await self._dispatch(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")
    
    async def _dispatch(self, event: Event) -> None:
        """Dispatch event to all matching subscribers."""
        handlers_to_call = []
        subscriptions_to_remove = []
        
        # Get specific subscribers
        for subscription in self._subscribers.get(event.type, []):
            if subscription.filter_fn and not subscription.filter_fn(event):
                continue
            handlers_to_call.append(subscription.handler)
            if subscription.once:
                subscriptions_to_remove.append((event.type, subscription))
        
        # Get all-event subscribers
        for subscription in self._all_subscribers:
            if subscription.filter_fn and not subscription.filter_fn(event):
                continue
            handlers_to_call.append(subscription.handler)
        
        # Call handlers
        for handler in handlers_to_call:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event.type.value}: {e}")
                self._dead_letters.append((event, str(e)))
        
        # Remove one-time subscriptions
        for event_type, subscription in subscriptions_to_remove:
            self._subscribers[event_type].remove(subscription)
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[Event]:
        """Get event history."""
        events = self._history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
        
        if since:
            events = [e for e in events if e.timestamp >= since]
        
        return events[-limit:]
    
    def get_dead_letters(self, limit: int = 100) -> list[tuple[Event, str]]:
        """Get failed events."""
        return self._dead_letters[-limit:]
    
    def clear_history(self) -> int:
        """Clear event history."""
        count = len(self._history)
        self._history.clear()
        return count
    
    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics."""
        return {
            "history_size": len(self._history),
            "dead_letters": len(self._dead_letters),
            "queue_size": self._queue.qsize(),
            "subscribers": {
                event_type.value: len(subs)
                for event_type, subs in self._subscribers.items()
            },
            "all_subscribers": len(self._all_subscribers),
            "processing": self._processing,
        }


# Convenience functions for global event bus
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


async def emit(event: Event) -> None:
    """Emit an event to the global bus."""
    await get_event_bus().publish(event)


def on(
    event_types: EventType | list[EventType],
    filter_fn: Optional[Callable[[Event], bool]] = None,
):
    """Decorator to subscribe a handler to events."""
    def decorator(handler: EventHandler):
        get_event_bus().subscribe(event_types, handler, filter_fn)
        return handler
    return decorator
