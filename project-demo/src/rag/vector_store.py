"""
FAISS Vector Store with Persistence.

Provides semantic search using FAISS with disk persistence.
"""

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from .chunker import Chunk
from .embedding_client import EmbeddingClient, EmbeddingResult


@dataclass
class SearchResult:
    """Result from a vector search."""
    chunk: Chunk
    score: float  # Similarity score (higher = more similar)
    rank: int


class FAISSVectorStore:
    """
    FAISS-based vector store with persistence.
    
    Uses L2 distance with normalized vectors (equivalent to cosine similarity).
    """
    
    def __init__(
        self,
        embedding_dim: int = 768,  # text-embedding-004 dimension
        persist_dir: Optional[str] = None,
    ):
        """
        Initialize vector store.
        
        Args:
            embedding_dim: Dimension of embedding vectors
            persist_dir: Directory for persistence (None = in-memory only)
        """
        if faiss is None:
            raise ImportError(
                "faiss-cpu is required for vector store. "
                "Install with: pip install faiss-cpu"
            )
        
        self.embedding_dim = embedding_dim
        self.persist_dir = Path(persist_dir) if persist_dir else None
        
        # Initialize FAISS index (using Inner Product for cosine similarity)
        self.index = faiss.IndexFlatIP(embedding_dim)
        
        # Store chunks for retrieval
        self.chunks: List[Chunk] = []
        
        # Embedding client for queries
        self.embedding_client = EmbeddingClient()
        
        # Stats
        self.index_cost = 0.0
        self.query_cost = 0.0
    
    def add_chunks(
        self,
        chunks: List[Chunk],
        embeddings: Optional[List[List[float]]] = None,
    ) -> float:
        """
        Add chunks to the index.
        
        Args:
            chunks: List of chunks to add
            embeddings: Pre-computed embeddings (optional)
            
        Returns:
            Cost of embedding generation
        """
        if not chunks:
            return 0.0
        
        cost = 0.0
        
        if embeddings is None:
            # Generate embeddings
            texts = [c.text for c in chunks]
            results = self.embedding_client.embed_batch(texts)
            embeddings = [r.embedding for r in results]
            cost = sum(r.cost for r in results)
            self.index_cost += cost
        
        # Normalize and add to index
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        
        self.index.add(vectors)
        self.chunks.extend(chunks)
        
        return cost
    
    def search(
        self,
        query: str,
        k: int = 5,
    ) -> Tuple[List[SearchResult], float]:
        """
        Search for similar chunks.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            Tuple of (results, query_cost)
        """
        # Embed query
        result = self.embedding_client.embed(query)
        self.query_cost += result.cost
        
        # Normalize query vector
        query_vector = np.array([result.embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)
        
        # Search
        k = min(k, len(self.chunks))
        if k == 0:
            return [], result.cost
        
        scores, indices = self.index.search(query_vector, k)
        
        # Build results
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx >= 0 and idx < len(self.chunks):
                results.append(SearchResult(
                    chunk=self.chunks[idx],
                    score=float(score),
                    rank=rank + 1,
                ))
        
        return results, result.cost
    
    def save(self, path: Optional[str] = None):
        """
        Save index and chunks to disk.
        
        Args:
            path: Directory to save to (uses persist_dir if not specified)
        """
        save_dir = Path(path) if path else self.persist_dir
        if save_dir is None:
            raise ValueError("No persist_dir specified")
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_dir / "index.faiss"))
        
        # Save chunks
        chunks_data = []
        for chunk in self.chunks:
            chunks_data.append({
                "text": chunk.text,
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "metadata": chunk.metadata,
            })
        
        with open(save_dir / "chunks.json", "w") as f:
            json.dump(chunks_data, f, indent=2)
        
        # Save metadata
        metadata = {
            "embedding_dim": self.embedding_dim,
            "num_chunks": len(self.chunks),
            "index_cost": self.index_cost,
        }
        with open(save_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved vector store to {save_dir} ({len(self.chunks)} chunks)")
    
    @classmethod
    def load(cls, path: str) -> "FAISSVectorStore":
        """
        Load index and chunks from disk.
        
        Args:
            path: Directory to load from
            
        Returns:
            Loaded FAISSVectorStore
        """
        load_dir = Path(path)
        
        # Load metadata
        with open(load_dir / "metadata.json") as f:
            metadata = json.load(f)
        
        # Create instance
        store = cls(
            embedding_dim=metadata["embedding_dim"],
            persist_dir=path,
        )
        store.index_cost = metadata.get("index_cost", 0.0)
        
        # Load FAISS index
        store.index = faiss.read_index(str(load_dir / "index.faiss"))
        
        # Load chunks
        with open(load_dir / "chunks.json") as f:
            chunks_data = json.load(f)
        
        for data in chunks_data:
            store.chunks.append(Chunk(
                text=data["text"],
                source=data["source"],
                chunk_index=data["chunk_index"],
                start_char=data["start_char"],
                end_char=data["end_char"],
                metadata=data.get("metadata"),
            ))
        
        print(f"Loaded vector store from {load_dir} ({len(store.chunks)} chunks)")
        return store
    
    def get_stats(self) -> dict:
        """Get vector store statistics."""
        return {
            "num_chunks": len(self.chunks),
            "embedding_dim": self.embedding_dim,
            "index_cost": round(self.index_cost, 6),
            "query_cost": round(self.query_cost, 6),
            "total_cost": round(self.index_cost + self.query_cost, 6),
            "embedding_stats": self.embedding_client.get_stats(),
        }
    
    def clear(self):
        """Clear the index and chunks."""
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.chunks = []
        self.index_cost = 0.0
        self.query_cost = 0.0
        self.embedding_client.reset()
