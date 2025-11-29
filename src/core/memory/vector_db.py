"""
Vector Database Integration

Integrates Qdrant or Pinecone for persistent vector storage and learning from past incidents.
"""

import asyncio
import logging
import os
from typing import Optional

from .base import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class VectorDB:
    """
    Vector database abstraction for persistent storage.
    
    Supports Qdrant (local/cloud) and Pinecone.
    """
    
    def __init__(self, provider: str = "qdrant", collection_name: str = "devops_brain_memory"):
        self.provider = provider
        self.collection_name = collection_name
        self._client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize vector database client."""
        if self.provider == "qdrant":
            await self._init_qdrant()
        elif self.provider == "pinecone":
            await self._init_pinecone()
        else:
            raise ValueError(f"Unknown vector DB provider: {self.provider}")
        
        self._initialized = True
        logger.info(f"Vector DB initialized: {self.provider}")
    
    async def _init_qdrant(self) -> None:
        """Initialize Qdrant client."""
        try:
            from qdrant_client import AsyncQdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # Get Qdrant URL (local or cloud)
            qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
            api_key = os.environ.get("QDRANT_API_KEY")
            
            self._client = AsyncQdrantClient(
                url=qdrant_url,
                api_key=api_key,
            )
            
            # Create collection if it doesn't exist
            collections = await self._client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                await self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            
        except ImportError:
            logger.error("qdrant-client not installed. Install with: pip install qdrant-client")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    async def _init_pinecone(self) -> None:
        """Initialize Pinecone client."""
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                raise ValueError("PINECONE_API_KEY environment variable required")
            
            self._client = Pinecone(api_key=api_key)
            
            # Create index if it doesn't exist
            index_name = self.collection_name
            if index_name not in [idx.name for idx in self._client.list_indexes()]:
                self._client.create_index(
                    name=index_name,
                    dimension=1536,  # OpenAI embedding size
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1",
                    ),
                )
                logger.info(f"Created Pinecone index: {index_name}")
            
        except ImportError:
            logger.error("pinecone-client not installed. Install with: pip install pinecone-client")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    async def store_incident_resolution(
        self,
        incident_id: str,
        description: str,
        resolution: str,
        embedding: list[float],
        metadata: dict,
    ) -> str:
        """
        Store an incident resolution for future learning.
        
        Args:
            incident_id: Unique incident identifier
            description: Incident description
            resolution: How it was resolved
            embedding: Vector embedding of description + resolution
            metadata: Additional metadata (agent, timestamp, etc.)
            
        Returns:
            Stored ID
        """
        if not self._initialized:
            await self.initialize()
        
        payload = {
            "incident_id": incident_id,
            "description": description,
            "resolution": resolution,
            "type": "incident_resolution",
            **metadata,
        }
        
        if self.provider == "qdrant":
            from qdrant_client.models import PointStruct
            
            point = PointStruct(
                id=incident_id,
                vector=embedding,
                payload=payload,
            )
            
            await self._client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
        
        elif self.provider == "pinecone":
            index = self._client.Index(self.collection_name)
            index.upsert(
                vectors=[(incident_id, embedding, payload)],
            )
        
        logger.info(f"Stored incident resolution: {incident_id}")
        return incident_id
    
    async def search_similar_incidents(
        self,
        query_embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict]:
        """
        Search for similar past incidents.
        
        Args:
            query_embedding: Vector embedding of current incident
            limit: Maximum results
            threshold: Similarity threshold
            
        Returns:
            List of similar incidents with resolutions
        """
        if not self._initialized:
            await self.initialize()
        
        if self.provider == "qdrant":
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            results = await self._client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="type",
                            match=MatchValue(value="incident_resolution"),
                        ),
                    ],
                ),
            )
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "description": hit.payload.get("description"),
                    "resolution": hit.payload.get("resolution"),
                    "metadata": {k: v for k, v in hit.payload.items() if k not in ["description", "resolution", "type"]},
                }
                for hit in results
            ]
        
        elif self.provider == "pinecone":
            index = self._client.Index(self.collection_name)
            results = index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                filter={"type": "incident_resolution"},
            )
            
            return [
                {
                    "id": match.id,
                    "score": match.score,
                    "description": match.metadata.get("description"),
                    "resolution": match.metadata.get("resolution"),
                    "metadata": {k: v for k, v in match.metadata.items() if k not in ["description", "resolution", "type"]},
                }
                for match in results.matches
                if match.score >= threshold
            ]
        
        return []
    
    async def store_agent_interaction(
        self,
        interaction_id: str,
        agent_name: str,
        task: str,
        result: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        """Store agent interaction for learning."""
        if not self._initialized:
            await self.initialize()
        
        payload = {
            "interaction_id": interaction_id,
            "agent_name": agent_name,
            "task": task,
            "result": result,
            "type": "agent_interaction",
            **metadata,
        }
        
        if self.provider == "qdrant":
            from qdrant_client.models import PointStruct
            
            point = PointStruct(
                id=interaction_id,
                vector=embedding,
                payload=payload,
            )
            
            await self._client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
        
        elif self.provider == "pinecone":
            index = self._client.Index(self.collection_name)
            index.upsert(
                vectors=[(interaction_id, embedding, payload)],
            )
