"""
RAG (Retrieval-Augmented Generation) Module.

Provides real embedding and vector store functionality for RAG pipelines:
- Vertex AI text-embedding integration
- FAISS vector store with persistence
- Document chunking utilities
- Embedding cost tracking
"""

from .embedding_client import (
    EmbeddingClient,
    EmbeddingResult,
    get_embedding,
    get_embeddings_batch,
)

from .vector_store import (
    FAISSVectorStore,
)

from .chunker import (
    Chunk,
    chunk_text,
    chunk_document,
)

from .cost_tracker import (
    RAGCostTracker,
)

__all__ = [
    # Embedding
    "EmbeddingClient",
    "EmbeddingResult",
    "get_embedding",
    "get_embeddings_batch",
    # Vector Store
    "FAISSVectorStore",
    # Chunking
    "Chunk",
    "chunk_text",
    "chunk_document",
    # Cost Tracking
    "RAGCostTracker",
]
