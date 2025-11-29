"""
Base Memory Interface

Abstract base class for memory implementations.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MemoryType(Enum):
    """Types of memory."""
    CONVERSATION = "conversation"  # Chat history
    WORKING = "working"  # Short-term task context
    EPISODIC = "episodic"  # Past experiences/events
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How to do things


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    memory_type: MemoryType = MemoryType.CONVERSATION
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    importance: float = 0.5  # 0-1 importance score
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "type": self.memory_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "access_count": self.access_count,
        }


@dataclass
class MemoryConfig:
    """Configuration for memory system."""
    max_entries: int = 1000
    max_tokens: int = 8000
    decay_rate: float = 0.01  # Memory decay over time
    importance_threshold: float = 0.3
    embedding_model: str = "text-embedding-3-small"
    persist: bool = True
    persist_path: Optional[str] = None


class BaseMemory(ABC):
    """
    Abstract base class for memory implementations.
    
    Provides interface for:
    - Storing and retrieving memories
    - Memory search and retrieval
    - Memory consolidation and pruning
    """
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self._entries: list[MemoryEntry] = []
    
    @abstractmethod
    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry."""
        pass
    
    @abstractmethod
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
    ) -> list[MemoryEntry]:
        """Search memories by query."""
        pass
    
    @abstractmethod
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
    ) -> list[MemoryEntry]:
        """Get recent memories."""
        pass
    
    @abstractmethod
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear memories."""
        pass
    
    async def add_conversation(
        self,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **metadata,
    ) -> str:
        """Convenience method to add conversation memory."""
        entry = MemoryEntry(
            content=content,
            memory_type=MemoryType.CONVERSATION,
            metadata={"role": role, **metadata},
            agent_id=agent_id,
            session_id=session_id,
        )
        return await self.add(entry)
    
    async def get_conversation_context(
        self,
        session_id: str,
        max_messages: int = 20,
        max_tokens: int = 4000,
    ) -> list[dict]:
        """Get conversation history formatted for LLM."""
        entries = await self.get_recent(
            limit=max_messages,
            memory_type=MemoryType.CONVERSATION,
        )
        
        # Filter by session
        entries = [e for e in entries if e.session_id == session_id]
        
        # Convert to messages
        messages = []
        total_tokens = 0
        
        for entry in reversed(entries):  # Oldest first
            role = entry.metadata.get("role", "user")
            msg = {"role": role, "content": entry.content}
            
            # Rough token estimate
            tokens = len(entry.content) // 4
            if total_tokens + tokens > max_tokens:
                break
            
            messages.append(msg)
            total_tokens += tokens
        
        return messages
    
    def calculate_importance(self, content: str, metadata: dict) -> float:
        """Calculate importance score for a memory."""
        importance = 0.5  # Base importance
        
        # Adjust based on content characteristics
        if len(content) > 500:
            importance += 0.1
        
        # Adjust based on metadata
        if metadata.get("is_error"):
            importance += 0.2
        if metadata.get("is_decision"):
            importance += 0.15
        if metadata.get("user_flagged"):
            importance += 0.3
        
        return min(importance, 1.0)
