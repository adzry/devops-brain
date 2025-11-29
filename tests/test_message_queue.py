"""
Tests for Message Queue

Unit tests for the message queue functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.core.message_queue import (
    MessageQueue,
    Message,
    MessagePriority,
    TopicMessageQueue,
)


class TestMessage:
    """Tests for Message dataclass."""
    
    def test_message_defaults(self):
        """Test default message values."""
        message = Message()
        
        assert message.id is not None
        assert message.priority == MessagePriority.MEDIUM
        assert message.payload == {}
        assert message.sender == ""
        assert message.recipient == ""
    
    def test_message_ordering(self):
        """Test message ordering by priority."""
        high = Message(priority=MessagePriority.HIGH)
        low = Message(priority=MessagePriority.LOW)
        
        # Higher priority (lower number) should come first
        assert high < low
    
    def test_message_ttl_not_expired(self):
        """Test message TTL when not expired."""
        message = Message(ttl_seconds=300)
        
        assert message.is_expired() is False
    
    def test_message_ttl_expired(self):
        """Test message TTL when expired."""
        message = Message(
            timestamp=datetime.utcnow() - timedelta(seconds=10),
            ttl_seconds=5,
        )
        
        assert message.is_expired() is True
    
    def test_message_no_ttl(self):
        """Test message without TTL never expires."""
        message = Message(
            timestamp=datetime.utcnow() - timedelta(days=100),
            ttl_seconds=None,
        )
        
        assert message.is_expired() is False


class TestMessageQueue:
    """Tests for MessageQueue."""
    
    @pytest.fixture
    def queue(self):
        """Create a message queue for testing."""
        return MessageQueue(max_size=10)
    
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, queue):
        """Test basic enqueue and dequeue."""
        message = Message(payload={"test": "data"})
        
        result = await queue.enqueue(message)
        assert result is True
        assert queue.size() == 1
        
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.payload["test"] == "data"
        assert queue.size() == 0
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self, queue):
        """Test that messages are dequeued by priority."""
        low = Message(priority=MessagePriority.LOW, payload={"priority": "low"})
        high = Message(priority=MessagePriority.HIGH, payload={"priority": "high"})
        critical = Message(priority=MessagePriority.CRITICAL, payload={"priority": "critical"})
        
        await queue.enqueue(low)
        await queue.enqueue(high)
        await queue.enqueue(critical)
        
        # Should get critical first
        msg1 = await queue.dequeue()
        assert msg1.payload["priority"] == "critical"
        
        msg2 = await queue.dequeue()
        assert msg2.payload["priority"] == "high"
        
        msg3 = await queue.dequeue()
        assert msg3.payload["priority"] == "low"
    
    @pytest.mark.asyncio
    async def test_max_size(self, queue):
        """Test queue max size enforcement."""
        # Fill the queue
        for i in range(10):
            await queue.enqueue(Message())
        
        # Should reject additional messages
        result = await queue.enqueue(Message())
        assert result is False
        assert queue.is_full()
    
    @pytest.mark.asyncio
    async def test_dequeue_timeout(self, queue):
        """Test dequeue timeout on empty queue."""
        result = await queue.dequeue(timeout=0.1)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_peek(self, queue):
        """Test peeking at the queue."""
        message = Message(payload={"test": "peek"})
        await queue.enqueue(message)
        
        # Peek should not remove the message
        peeked = await queue.peek()
        assert peeked is not None
        assert peeked.payload["test"] == "peek"
        assert queue.size() == 1
    
    @pytest.mark.asyncio
    async def test_clear(self, queue):
        """Test clearing the queue."""
        for i in range(5):
            await queue.enqueue(Message())
        
        count = await queue.clear()
        
        assert count == 5
        assert queue.size() == 0
        assert queue.is_empty()
    
    @pytest.mark.asyncio
    async def test_remove_expired(self, queue):
        """Test removing expired messages."""
        # Add some expired messages
        expired = Message(
            timestamp=datetime.utcnow() - timedelta(seconds=10),
            ttl_seconds=5,
        )
        valid = Message(ttl_seconds=300)
        
        await queue.enqueue(expired)
        await queue.enqueue(valid)
        
        removed = await queue.remove_expired()
        
        assert removed == 1
        assert queue.size() == 1
    
    def test_get_stats(self, queue):
        """Test getting queue statistics."""
        stats = queue.get_stats()
        
        assert "current_size" in stats
        assert "max_size" in stats
        assert "total_enqueued" in stats
        assert "total_processed" in stats
        assert "by_priority" in stats
        assert "utilization" in stats


class TestTopicMessageQueue:
    """Tests for TopicMessageQueue."""
    
    @pytest.fixture
    def topic_queue(self):
        """Create a topic message queue for testing."""
        return TopicMessageQueue()
    
    @pytest.mark.asyncio
    async def test_create_topic(self, topic_queue):
        """Test creating a topic."""
        await topic_queue.create_topic("test_topic")
        
        assert "test_topic" in topic_queue.list_topics()
    
    @pytest.mark.asyncio
    async def test_publish_consume(self, topic_queue):
        """Test publish and consume."""
        await topic_queue.create_topic("test_topic")
        
        message = Message(payload={"data": "test"})
        result = await topic_queue.publish("test_topic", message)
        
        assert result is True
        
        consumed = await topic_queue.consume("test_topic")
        assert consumed is not None
        assert consumed.payload["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_subscribe(self, topic_queue):
        """Test subscription."""
        await topic_queue.subscribe("events", "subscriber1")
        
        stats = topic_queue.get_topic_stats("events")
        assert stats is not None
        assert stats["subscribers"] == 1
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, topic_queue):
        """Test unsubscription."""
        await topic_queue.subscribe("events", "subscriber1")
        await topic_queue.unsubscribe("events", "subscriber1")
        
        stats = topic_queue.get_topic_stats("events")
        assert stats["subscribers"] == 0
    
    @pytest.mark.asyncio
    async def test_delete_topic(self, topic_queue):
        """Test deleting a topic."""
        await topic_queue.create_topic("temp_topic")
        await topic_queue.delete_topic("temp_topic")
        
        assert "temp_topic" not in topic_queue.list_topics()
