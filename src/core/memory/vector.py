"""
Vector Memory

Semantic memory using vector embeddings for similarity search.
"""

import asyncio
import logging
import math
from datetime import datetime
from typing import Optional

from .base import BaseMemory, MemoryConfig, MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class VectorMemory(BaseMemory):
    """
    Vector-based semantic memory using embeddings.
    
    Features:
    - Semantic similarity search
    - Automatic embedding generation
    - Efficient nearest neighbor search
    - Memory consolidation
    """
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        self._embeddings: dict[str, list[float]] = {}
        self._embedding_client = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize embedding client."""
        try:
            from openai import AsyncOpenAI
            import os
            
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self._embedding_client = AsyncOpenAI(api_key=api_key)
                logger.info("Vector memory initialized with OpenAI embeddings")
            else:
                logger.warning("No OpenAI API key, using mock embeddings")
        except ImportError:
            logger.warning("OpenAI not installed, using mock embeddings")
    
    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry with embedding."""
        async with self._lock:
            # Generate embedding
            entry.embedding = await self._get_embedding(entry.content)
            self._embeddings[entry.id] = entry.embedding
            
            # Calculate importance
            entry.importance = self.calculate_importance(entry.content, entry.metadata)
            
            self._entries.append(entry)
            
            # Prune if needed
            await self._maybe_prune()
            
            logger.debug(f"Added vector memory entry {entry.id}")
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
        similarity_threshold: float = 0.5,
    ) -> list[MemoryEntry]:
        """Search memories by semantic similarity."""
        query_embedding = await self._get_embedding(query)
        
        results = []
        for entry in self._entries:
            if memory_type and entry.memory_type != memory_type:
                continue
            
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity >= similarity_threshold:
                    results.append((entry, similarity))
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        return [entry for entry, _ in results[:limit]]
    
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
    ) -> list[MemoryEntry]:
        """Get recent memories."""
        entries = self._entries
        
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)
        return entries[:limit]
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear memories."""
        async with self._lock:
            if memory_type:
                to_remove = [e for e in self._entries if e.memory_type == memory_type]
                for entry in to_remove:
                    self._entries.remove(entry)
                    self._embeddings.pop(entry.id, None)
                return len(to_remove)
            else:
                count = len(self._entries)
                self._entries.clear()
                self._embeddings.clear()
                return count
    
    async def find_related(
        self,
        entry_id: str,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Find memories related to a specific entry."""
        entry = await self.get(entry_id)
        if not entry or not entry.embedding:
            return []
        
        results = []
        for other in self._entries:
            if other.id == entry_id:
                continue
            
            if other.embedding:
                similarity = self._cosine_similarity(entry.embedding, other.embedding)
                results.append((other, similarity))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in results[:limit]]
    
    async def consolidate(self) -> int:
        """Consolidate similar memories to reduce redundancy."""
        async with self._lock:
            consolidated = 0
            to_remove = set()
            
            for i, entry1 in enumerate(self._entries):
                if entry1.id in to_remove:
                    continue
                
                for entry2 in self._entries[i + 1:]:
                    if entry2.id in to_remove:
                        continue
                    
                    if entry1.embedding and entry2.embedding:
                        similarity = self._cosine_similarity(
                            entry1.embedding, entry2.embedding
                        )
                        
                        if similarity > 0.95:  # Very similar
                            # Keep the one with higher importance/access
                            if entry2.importance > entry1.importance:
                                to_remove.add(entry1.id)
                            else:
                                to_remove.add(entry2.id)
                            consolidated += 1
            
            # Remove consolidated entries
            self._entries = [e for e in self._entries if e.id not in to_remove]
            for entry_id in to_remove:
                self._embeddings.pop(entry_id, None)
            
            logger.info(f"Consolidated {consolidated} similar memories")
            return consolidated
    
    async def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        if self._embedding_client:
            try:
                response = await self._embedding_client.embeddings.create(
                    model=self.config.embedding_model,
                    input=text[:8000],  # Truncate if too long
                )
                return response.data[0].embedding
            except Exception as e:
                logger.warning(f"Embedding API failed: {e}, using mock")
        
        # Mock embedding (random but deterministic)
        return self._mock_embedding(text)
    
    def _mock_embedding(self, text: str, dim: int = 1536) -> list[float]:
        """Generate deterministic mock embedding."""
        import hashlib
        
        # Create deterministic "embedding" from text hash
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        embedding = []
        
        for i in range(0, min(len(text_hash), dim * 2), 2):
            val = int(text_hash[i:i+2], 16) / 255.0 - 0.5
            embedding.append(val)
        
        # Pad or truncate to dimension
        while len(embedding) < dim:
            embedding.extend(embedding[:dim - len(embedding)])
        
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding[:dim]
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def _maybe_prune(self) -> None:
        """Prune old/low-importance memories if over limit."""
        if len(self._entries) <= self.config.max_entries:
            return
        
        # Calculate scores combining importance, recency, and access
        now = datetime.utcnow()
        scored = []
        
        for entry in self._entries:
            age_hours = (now - entry.timestamp).total_seconds() / 3600
            recency_score = math.exp(-self.config.decay_rate * age_hours)
            access_score = min(entry.access_count / 10, 1.0)
            
            score = (
                entry.importance * 0.4 +
                recency_score * 0.4 +
                access_score * 0.2
            )
            scored.append((entry, score))
        
        # Keep top entries
        scored.sort(key=lambda x: x[1], reverse=True)
        keep = scored[:self.config.max_entries]
        
        self._entries = [e for e, _ in keep]
        kept_ids = {e.id for e in self._entries}
        
        # Clean up embeddings
        for entry_id in list(self._embeddings.keys()):
            if entry_id not in kept_ids:
                del self._embeddings[entry_id]
