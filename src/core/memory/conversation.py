"""
Conversation Memory

Manages conversation history with token-aware windowing.
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Optional

from .base import BaseMemory, MemoryConfig, MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class ConversationMemory(BaseMemory):
    """
    Conversation-focused memory implementation.
    
    Features:
    - Token-aware context window
    - Automatic summarization of old messages
    - Session management
    - Message importance scoring
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        self._sessions: dict[str, deque[MemoryEntry]] = {}
        self._summaries: dict[str, str] = {}
        self._lock = asyncio.Lock()
    
    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry."""
        async with self._lock:
            session_id = entry.session_id or "default"
            
            if session_id not in self._sessions:
                self._sessions[session_id] = deque(maxlen=self.config.max_entries)
            
            # Calculate importance
            entry.importance = self.calculate_importance(entry.content, entry.metadata)
            
            self._sessions[session_id].append(entry)
            self._entries.append(entry)
            
            # Check if we need to summarize old messages
            await self._maybe_summarize(session_id)
            
            logger.debug(f"Added memory entry {entry.id} to session {session_id}")
            return entry.id
    
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID."""
        for entry in self._entries:
            if entry.id == entry_id:
                entry.access_count += 1
                entry.last_accessed = datetime.utcnow()
                return entry
        return None
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
    ) -> list[MemoryEntry]:
        """Search memories by keyword matching."""
        query_lower = query.lower()
        results = []
        
        for entry in self._entries:
            if memory_type and entry.memory_type != memory_type:
                continue
            
            # Simple keyword matching (use vector search for better results)
            if query_lower in entry.content.lower():
                results.append(entry)
                entry.access_count += 1
                entry.last_accessed = datetime.utcnow()
        
        # Sort by relevance (importance + recency)
        results.sort(
            key=lambda e: (e.importance, e.timestamp),
            reverse=True,
        )
        
        return results[:limit]
    
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        session_id: Optional[str] = None,
    ) -> list[MemoryEntry]:
        """Get recent memories."""
        entries = self._entries
        
        if session_id and session_id in self._sessions:
            entries = list(self._sessions[session_id])
        
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        
        # Sort by timestamp descending
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)
        
        return entries[:limit]
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear memories."""
        async with self._lock:
            if memory_type:
                original_count = len(self._entries)
                self._entries = [e for e in self._entries if e.memory_type != memory_type]
                return original_count - len(self._entries)
            else:
                count = len(self._entries)
                self._entries.clear()
                self._sessions.clear()
                self._summaries.clear()
                return count
    
    async def get_context_for_prompt(
        self,
        session_id: str,
        max_tokens: int = 4000,
        include_summary: bool = True,
    ) -> str:
        """Get formatted context for prompt injection."""
        context_parts = []
        
        # Add summary if available
        if include_summary and session_id in self._summaries:
            context_parts.append(f"Previous conversation summary:\n{self._summaries[session_id]}\n")
        
        # Add recent messages
        messages = await self.get_conversation_context(
            session_id=session_id,
            max_tokens=max_tokens,
        )
        
        for msg in messages:
            role = msg["role"].capitalize()
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    async def _maybe_summarize(self, session_id: str) -> None:
        """Summarize old messages if session is getting long."""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        # Check if we need summarization
        total_tokens = sum(len(e.content) // 4 for e in session)
        
        if total_tokens > self.config.max_tokens * 0.8:
            # Keep recent messages, summarize old ones
            messages_to_summarize = []
            keep_count = len(session) // 2
            
            while len(session) > keep_count:
                messages_to_summarize.append(session.popleft())
            
            # Create summary (in production, use LLM)
            summary_content = self._create_summary(messages_to_summarize)
            self._summaries[session_id] = summary_content
            
            logger.info(f"Summarized {len(messages_to_summarize)} messages for session {session_id}")
    
    def _create_summary(self, entries: list[MemoryEntry]) -> str:
        """Create a summary of messages (placeholder - use LLM in production)."""
        # Simple extractive summary
        key_points = []
        
        for entry in entries:
            if entry.importance > 0.6:
                key_points.append(f"- {entry.content[:100]}...")
        
        if not key_points:
            # Take first and last message
            if entries:
                key_points.append(f"Started with: {entries[0].content[:100]}...")
            if len(entries) > 1:
                key_points.append(f"Ended with: {entries[-1].content[:100]}...")
        
        return "Key points from previous conversation:\n" + "\n".join(key_points)
    
    async def create_session(self, session_id: str) -> None:
        """Create a new conversation session."""
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = deque(maxlen=self.config.max_entries)
                logger.info(f"Created new session: {session_id}")
    
    async def end_session(self, session_id: str) -> Optional[str]:
        """End a session and return summary."""
        async with self._lock:
            if session_id not in self._sessions:
                return None
            
            # Create final summary
            entries = list(self._sessions[session_id])
            summary = self._create_summary(entries)
            
            # Store as episodic memory
            await self.add(MemoryEntry(
                content=summary,
                memory_type=MemoryType.EPISODIC,
                metadata={"session_id": session_id, "type": "session_summary"},
            ))
            
            # Clean up
            del self._sessions[session_id]
            if session_id in self._summaries:
                del self._summaries[session_id]
            
            logger.info(f"Ended session: {session_id}")
            return summary
    
    def get_session_stats(self, session_id: str) -> dict:
        """Get statistics for a session."""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        entries = list(session)
        return {
            "session_id": session_id,
            "message_count": len(entries),
            "total_tokens": sum(len(e.content) // 4 for e in entries),
            "has_summary": session_id in self._summaries,
            "oldest_message": entries[0].timestamp.isoformat() if entries else None,
            "newest_message": entries[-1].timestamp.isoformat() if entries else None,
        }
