"""
Google GenAI Embedding Client.

Integrates with Google's text-embedding-004 model for semantic embeddings
using the google-genai SDK (same as the main LLM client).

Tracks embedding costs for RAG cost analysis.
"""

import time
from dataclasses import dataclass
from typing import List, Optional

from google import genai

from ..config import GCP_PROJECT_ID, GCP_REGION


# Pricing for text-embedding-004 (per 1K characters)
# Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
EMBEDDING_COST_PER_1K_CHARS = 0.000025  # $0.025 per 1M characters

# Embedding model
EMBEDDING_MODEL = "text-embedding-004"


@dataclass
class EmbeddingResult:
    """Result from embedding a text."""
    text: str
    embedding: List[float]
    model: str
    cost: float
    latency_ms: int
    char_count: int


# Module-level client instance
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Get or create the GenAI client."""
    global _client
    if _client is None:
        if not GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID not set. Check your .env file.")
        _client = genai.Client(
            vertexai=True,
            project=GCP_PROJECT_ID,
            location=GCP_REGION
        )
    return _client


def get_embedding(text: str) -> EmbeddingResult:
    """
    Get embedding for a single text.
    
    Args:
        text: Text to embed
        
    Returns:
        EmbeddingResult with embedding vector and cost info
    """
    client = _get_client()
    
    start_time = time.perf_counter()
    
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    
    end_time = time.perf_counter()
    
    latency_ms = int((end_time - start_time) * 1000)
    char_count = len(text)
    cost = (char_count / 1000) * EMBEDDING_COST_PER_1K_CHARS
    
    # Extract embedding from response
    embedding = response.embeddings[0].values
    
    return EmbeddingResult(
        text=text,
        embedding=list(embedding),
        model=EMBEDDING_MODEL,
        cost=cost,
        latency_ms=latency_ms,
        char_count=char_count,
    )


def get_embeddings_batch(texts: List[str], batch_size: int = 100) -> List[EmbeddingResult]:
    """
    Get embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts per API call
        
    Returns:
        List of EmbeddingResults
    """
    client = _get_client()
    results = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        start_time = time.perf_counter()
        
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
        )
        
        end_time = time.perf_counter()
        
        latency_ms = int((end_time - start_time) * 1000)
        latency_per_item = latency_ms // len(batch)
        
        for j, text in enumerate(batch):
            char_count = len(text)
            cost = (char_count / 1000) * EMBEDDING_COST_PER_1K_CHARS
            
            results.append(EmbeddingResult(
                text=text,
                embedding=list(response.embeddings[j].values),
                model=EMBEDDING_MODEL,
                cost=cost,
                latency_ms=latency_per_item,
                char_count=char_count,
            ))
    
    return results


class EmbeddingClient:
    """
    Client for managing embeddings with cost tracking.
    """
    
    def __init__(self):
        self.total_cost = 0.0
        self.total_chars = 0
        self.total_requests = 0
        self.total_latency_ms = 0
    
    def embed(self, text: str) -> EmbeddingResult:
        """Embed single text with tracking."""
        result = get_embedding(text)
        self._track(result)
        return result
    
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Embed multiple texts with tracking."""
        results = get_embeddings_batch(texts)
        for r in results:
            self._track(r)
        return results
    
    def _track(self, result: EmbeddingResult):
        """Track embedding costs."""
        self.total_cost += result.cost
        self.total_chars += result.char_count
        self.total_requests += 1
        self.total_latency_ms += result.latency_ms
    
    def get_stats(self) -> dict:
        """Get embedding statistics."""
        return {
            "total_cost": round(self.total_cost, 6),
            "total_chars": self.total_chars,
            "total_requests": self.total_requests,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.total_latency_ms // max(1, self.total_requests),
        }
    
    def reset(self):
        """Reset tracking."""
        self.total_cost = 0.0
        self.total_chars = 0
        self.total_requests = 0
        self.total_latency_ms = 0


if __name__ == "__main__":
    print("Testing embedding client...")
    
    test_text = "Machine learning is a subset of artificial intelligence."
    result = get_embedding(test_text)
    
    print(f"✓ Embedding generated")
    print(f"  Dimensions: {len(result.embedding)}")
    print(f"  Cost: ${result.cost:.6f}")
    print(f"  Latency: {result.latency_ms}ms")
