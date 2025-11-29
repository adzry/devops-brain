"""
Memory Manager

Unified interface for managing different memory types.
"""

import asyncio
import logging
from typing import Any, Optional

from .base import MemoryConfig, MemoryEntry, MemoryType
from .conversation import ConversationMemory
from .vector import VectorMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Unified memory manager for agents.
    
    Combines different memory types:
    - Conversation memory for chat history
    - Vector memory for semantic search
    - Working memory for current task context
    """
    
    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        agent_id: Optional[str] = None,
    ):
        self.config = config or MemoryConfig()
        self.agent_id = agent_id
        
        # Initialize memory stores
        self.conversation = ConversationMemory(self.config)
        self.semantic = VectorMemory(self.config)
        
        # Working memory (short-term, current task)
        self._working_memory: dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize all memory systems."""
        await self.semantic.initialize()
        logger.info(f"Memory manager initialized for agent {self.agent_id}")
    
    # ========================================================================
    # Conversation Memory
    # ========================================================================
    
    async def add_message(
        self,
        role: str,
        content: str,
        session_id: str,
        **metadata,
    ) -> str:
        """Add a conversation message."""
        return await self.conversation.add_conversation(
            role=role,
            content=content,
            agent_id=self.agent_id,
            session_id=session_id,
            **metadata,
        )
    
    async def get_conversation(
        self,
        session_id: str,
        max_messages: int = 20,
        max_tokens: int = 4000,
    ) -> list[dict]:
        """Get conversation history for LLM."""
        return await self.conversation.get_conversation_context(
            session_id=session_id,
            max_messages=max_messages,
            max_tokens=max_tokens,
        )
    
    async def get_context_prompt(
        self,
        session_id: str,
        max_tokens: int = 4000,
    ) -> str:
        """Get formatted context for prompt."""
        return await self.conversation.get_context_for_prompt(
            session_id=session_id,
            max_tokens=max_tokens,
        )
    
    # ========================================================================
    # Semantic Memory
    # ========================================================================
    
    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        **metadata,
    ) -> str:
        """Store a memory with semantic embedding."""
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            metadata=metadata,
            agent_id=self.agent_id,
        )
        return await self.semantic.add(entry)
    
    async def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
    ) -> list[MemoryEntry]:
        """Recall relevant memories."""
        return await self.semantic.search(
            query=query,
            limit=limit,
            memory_type=memory_type,
        )
    
    async def get_relevant_context(
        self,
        query: str,
        max_entries: int = 5,
        max_tokens: int = 2000,
    ) -> str:
        """Get relevant memories formatted as context."""
        memories = await self.recall(query, limit=max_entries)
        
        context_parts = []
        total_tokens = 0
        
        for memory in memories:
            tokens = len(memory.content) // 4
            if total_tokens + tokens > max_tokens:
                break
            
            context_parts.append(f"- {memory.content}")
            total_tokens += tokens
        
        if not context_parts:
            return ""
        
        return "Relevant context from memory:\n" + "\n".join(context_parts)
    
    # ========================================================================
    # Working Memory
    # ========================================================================
    
    async def set_working(self, key: str, value: Any) -> None:
        """Set working memory value."""
        async with self._lock:
            self._working_memory[key] = value
    
    async def get_working(self, key: str, default: Any = None) -> Any:
        """Get working memory value."""
        return self._working_memory.get(key, default)
    
    async def clear_working(self) -> None:
        """Clear working memory."""
        async with self._lock:
            self._working_memory.clear()
    
    async def get_working_context(self) -> dict:
        """Get all working memory as context."""
        return dict(self._working_memory)
    
    # ========================================================================
    # Unified Operations
    # ========================================================================
    
    async def build_context(
        self,
        session_id: str,
        current_query: Optional[str] = None,
        max_conversation_tokens: int = 3000,
        max_memory_tokens: int = 1000,
    ) -> dict:
        """
        Build comprehensive context for agent.
        
        Combines:
        - Conversation history
        - Relevant semantic memories
        - Working memory
        """
        context = {
            "conversation": [],
            "memories": "",
            "working": {},
        }
        
        # Get conversation
        context["conversation"] = await self.get_conversation(
            session_id=session_id,
            max_tokens=max_conversation_tokens,
        )
        
        # Get relevant memories if query provided
        if current_query:
            context["memories"] = await self.get_relevant_context(
                query=current_query,
                max_tokens=max_memory_tokens,
            )
        
        # Get working memory
        context["working"] = await self.get_working_context()
        
        return context
    
    async def save_interaction(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Save a complete interaction."""
        metadata = metadata or {}
        
        # Save to conversation memory
        await self.add_message(
            role="user",
            content=user_message,
            session_id=session_id,
            **metadata,
        )
        
        await self.add_message(
            role="assistant",
            content=assistant_response,
            session_id=session_id,
            **metadata,
        )
        
        # Optionally save important info to semantic memory
        if metadata.get("important"):
            await self.remember(
                content=f"User asked: {user_message}\nResponse: {assistant_response[:500]}",
                memory_type=MemoryType.EPISODIC,
                session_id=session_id,
            )
    
    async def cleanup(self) -> dict:
        """Cleanup and consolidate memories."""
        results = {
            "semantic_consolidated": await self.semantic.consolidate(),
        }
        return results
    
    def get_stats(self) -> dict:
        """Get memory statistics."""
        return {
            "agent_id": self.agent_id,
            "conversation_entries": len(self.conversation._entries),
            "semantic_entries": len(self.semantic._entries),
            "working_memory_keys": len(self._working_memory),
            "sessions": list(self.conversation._sessions.keys()),
        }
