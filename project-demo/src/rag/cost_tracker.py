"""
RAG Cost Tracker.

Tracks embedding and retrieval costs for RAG pipelines.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class RAGCostEntry:
    """A single RAG cost event."""
    timestamp: str
    operation: str  # "index", "query", "rerank"
    cost: float
    char_count: int
    latency_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGCostTracker:
    """
    Track RAG-related costs across operations.
    """
    
    def __init__(self):
        self.entries: List[RAGCostEntry] = []
        self._index_cost = 0.0
        self._query_cost = 0.0
        self._rerank_cost = 0.0
    
    def track_index(
        self,
        cost: float,
        char_count: int,
        latency_ms: int,
        num_chunks: int = 0,
    ):
        """Track index building cost."""
        self._index_cost += cost
        self.entries.append(RAGCostEntry(
            timestamp=datetime.now().isoformat(),
            operation="index",
            cost=cost,
            char_count=char_count,
            latency_ms=latency_ms,
            metadata={"num_chunks": num_chunks},
        ))
    
    def track_query(
        self,
        cost: float,
        char_count: int,
        latency_ms: int,
        num_results: int = 0,
    ):
        """Track query embedding cost."""
        self._query_cost += cost
        self.entries.append(RAGCostEntry(
            timestamp=datetime.now().isoformat(),
            operation="query",
            cost=cost,
            char_count=char_count,
            latency_ms=latency_ms,
            metadata={"num_results": num_results},
        ))
    
    def track_rerank(
        self,
        cost: float,
        char_count: int,
        latency_ms: int,
    ):
        """Track reranking cost (if using LLM for reranking)."""
        self._rerank_cost += cost
        self.entries.append(RAGCostEntry(
            timestamp=datetime.now().isoformat(),
            operation="rerank",
            cost=cost,
            char_count=char_count,
            latency_ms=latency_ms,
        ))
    
    @property
    def total_cost(self) -> float:
        """Total RAG cost."""
        return self._index_cost + self._query_cost + self._rerank_cost
    
    @property
    def index_cost(self) -> float:
        """Total indexing cost."""
        return self._index_cost
    
    @property
    def query_cost(self) -> float:
        """Total query cost."""
        return self._query_cost
    
    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "total_cost": round(self.total_cost, 6),
            "index_cost": round(self._index_cost, 6),
            "query_cost": round(self._query_cost, 6),
            "rerank_cost": round(self._rerank_cost, 6),
            "num_operations": len(self.entries),
            "operations_by_type": {
                "index": sum(1 for e in self.entries if e.operation == "index"),
                "query": sum(1 for e in self.entries if e.operation == "query"),
                "rerank": sum(1 for e in self.entries if e.operation == "rerank"),
            },
        }
    
    def reset(self):
        """Reset all tracking."""
        self.entries = []
        self._index_cost = 0.0
        self._query_cost = 0.0
        self._rerank_cost = 0.0
