"""
Message Queue

In-memory message queue with priority support for agent communication.
Can be extended to use Redis, RabbitMQ, or other backends.
"""

import asyncio
import heapq
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MessagePriority(IntEnum):
    """Message priority levels (lower number = higher priority)."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass(order=True)
class Message:
    """
    Message for inter-agent communication.
    
    Ordered by priority (lower = higher priority) then by timestamp.
    """
    
    priority: MessagePriority = field(compare=True, default=MessagePriority.MEDIUM)
    timestamp: datetime = field(compare=True, default_factory=datetime.utcnow)
    id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4()))
    payload: dict[str, Any] = field(compare=False, default_factory=dict)
    sender: str = field(compare=False, default="")
    recipient: str = field(compare=False, default="")
    reply_to: Optional[str] = field(compare=False, default=None)
    ttl_seconds: Optional[int] = field(compare=False, default=None)
    metadata: dict[str, Any] = field(compare=False, default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.utcnow() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


class MessageQueue:
    """
    Priority-based message queue for agent communication.
    
    Features:
    - Priority ordering (critical > high > medium > low)
    - FIFO within same priority
    - TTL support for message expiration
    - Async operations
    """
    
    def __init__(self, max_size: int = 10000):
        self._queue: list[Message] = []
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Event()
        self._message_count = 0
        self._processed_count = 0
        
        logger.info(f"MessageQueue initialized with max_size={max_size}")
    
    async def enqueue(self, message: Message) -> bool:
        """
        Add a message to the queue.
        
        Args:
            message: Message to enqueue
            
        Returns:
            True if message was enqueued, False if queue is full
        """
        async with self._lock:
            if len(self._queue) >= self._max_size:
                logger.warning("Queue is full, message rejected")
                return False
            
            heapq.heappush(self._queue, message)
            self._message_count += 1
            self._not_empty.set()
            
            logger.debug(
                f"Message {message.id} enqueued with priority {message.priority.name}"
            )
            return True
    
    async def dequeue(self, timeout: Optional[float] = 0.1) -> Optional[Message]:
        """
        Get the next message from the queue.
        
        Args:
            timeout: How long to wait for a message (None = wait forever)
            
        Returns:
            Next message or None if timeout
        """
        try:
            await asyncio.wait_for(self._not_empty.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        
        async with self._lock:
            if not self._queue:
                self._not_empty.clear()
                return None
            
            # Get next message
            message = heapq.heappop(self._queue)
            
            # Skip expired messages
            while message.is_expired() and self._queue:
                logger.debug(f"Skipping expired message: {message.id}")
                message = heapq.heappop(self._queue)
            
            if message.is_expired():
                self._not_empty.clear()
                return None
            
            if not self._queue:
                self._not_empty.clear()
            
            self._processed_count += 1
            logger.debug(f"Message {message.id} dequeued")
            return message
    
    async def peek(self) -> Optional[Message]:
        """Peek at the next message without removing it."""
        async with self._lock:
            if self._queue:
                return self._queue[0]
            return None
    
    def size(self) -> int:
        """Get current queue size."""
        return len(self._queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._queue) == 0
    
    def is_full(self) -> bool:
        """Check if queue is full."""
        return len(self._queue) >= self._max_size
    
    async def clear(self) -> int:
        """Clear all messages from the queue."""
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._not_empty.clear()
            logger.info(f"Queue cleared, {count} messages removed")
            return count
    
    async def remove_expired(self) -> int:
        """Remove all expired messages."""
        async with self._lock:
            original_count = len(self._queue)
            self._queue = [m for m in self._queue if not m.is_expired()]
            heapq.heapify(self._queue)
            removed = original_count - len(self._queue)
            
            if removed > 0:
                logger.info(f"Removed {removed} expired messages")
            
            return removed
    
    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        priority_counts = {p.name: 0 for p in MessagePriority}
        for msg in self._queue:
            priority_counts[msg.priority.name] += 1
        
        return {
            "current_size": len(self._queue),
            "max_size": self._max_size,
            "total_enqueued": self._message_count,
            "total_processed": self._processed_count,
            "by_priority": priority_counts,
            "utilization": len(self._queue) / self._max_size,
        }


class TopicMessageQueue:
    """
    Topic-based message queue for pub/sub communication.
    
    Allows agents to subscribe to specific topics and receive
    only relevant messages.
    """
    
    def __init__(self):
        self._topics: dict[str, MessageQueue] = {}
        self._subscribers: dict[str, set[str]] = {}  # topic -> set of subscriber IDs
        self._lock = asyncio.Lock()
    
    async def create_topic(self, topic: str) -> None:
        """Create a new topic."""
        async with self._lock:
            if topic not in self._topics:
                self._topics[topic] = MessageQueue()
                self._subscribers[topic] = set()
                logger.info(f"Topic created: {topic}")
    
    async def delete_topic(self, topic: str) -> None:
        """Delete a topic and all its messages."""
        async with self._lock:
            self._topics.pop(topic, None)
            self._subscribers.pop(topic, None)
            logger.info(f"Topic deleted: {topic}")
    
    async def subscribe(self, topic: str, subscriber_id: str) -> None:
        """Subscribe to a topic."""
        async with self._lock:
            if topic not in self._topics:
                await self.create_topic(topic)
            self._subscribers[topic].add(subscriber_id)
            logger.debug(f"Subscriber {subscriber_id} subscribed to {topic}")
    
    async def unsubscribe(self, topic: str, subscriber_id: str) -> None:
        """Unsubscribe from a topic."""
        async with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic].discard(subscriber_id)
    
    async def publish(self, topic: str, message: Message) -> bool:
        """Publish a message to a topic."""
        async with self._lock:
            if topic not in self._topics:
                await self.create_topic(topic)
            return await self._topics[topic].enqueue(message)
    
    async def consume(
        self,
        topic: str,
        timeout: Optional[float] = 0.1,
    ) -> Optional[Message]:
        """Consume a message from a topic."""
        if topic not in self._topics:
            return None
        return await self._topics[topic].dequeue(timeout)
    
    def list_topics(self) -> list[str]:
        """List all topics."""
        return list(self._topics.keys())
    
    def get_topic_stats(self, topic: str) -> Optional[dict[str, Any]]:
        """Get statistics for a topic."""
        if topic not in self._topics:
            return None
        
        stats = self._topics[topic].get_stats()
        stats["subscribers"] = len(self._subscribers.get(topic, set()))
        return stats
