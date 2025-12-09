"""
Pipeline implementations for different LLM workflows.

Contains:
- Linear/multi-stage pipelines
- Agentic patterns (ReAct, multi-turn, self-correcting)
- RAG pipelines with real embedding retrieval
- Streaming with TTFT metrics
"""

# Base classes and types
from .base import (
    StageType,
    LoopTermination,
    StageResult,
    PipelineResult,
    PipelineStage,
    Pipeline,
)

# Agentic pipelines
from .agentic import (
    ReActPipeline,
    MultiTurnPipeline,
    SelfCorrectingPipeline,
)

# RAG pipeline
from .rag import RAGPipeline

# Registry and pre-defined pipelines
from .registry import (
    # Registry functions
    PIPELINES,
    get_pipeline,
    list_pipelines,
    # Standard pipelines
    VERBOSITY_CONCISE_PIPELINE,
    VERBOSITY_COT_PIPELINE,
    HYBRID_COT_PIPELINE,
    CONTEXT_SHORT_PIPELINE,
    CONTEXT_LONG_PIPELINE,
    # Agentic pipelines
    REACT_RESEARCH_PIPELINE,
    REACT_HYBRID_PIPELINE,
    MULTITURN_SHORT_PIPELINE,
    MULTITURN_LONG_PIPELINE,
    SELF_CORRECTING_PIPELINE,
    SELF_CORRECTING_HYBRID_PIPELINE,
    # RAG pipelines
    RAG_BASIC_PIPELINE,
    RAG_VERIFIED_PIPELINE,
    RAG_HYBRID_PIPELINE,
    # Document analysis pipelines
    DOC_ANALYSIS_SIMPLE_PIPELINE,
    DOC_ANALYSIS_THOROUGH_PIPELINE,
    DOC_ANALYSIS_ITERATIVE_PIPELINE,
    DOC_ANALYSIS_HYBRID_PIPELINE,
)

__all__ = [
    # Base types
    "StageType",
    "LoopTermination",
    "StageResult",
    "PipelineResult",
    "PipelineStage",
    "Pipeline",
    # Agentic classes
    "ReActPipeline",
    "MultiTurnPipeline",
    "SelfCorrectingPipeline",
    # RAG class
    "RAGPipeline",
    # Registry
    "PIPELINES",
    "get_pipeline",
    "list_pipelines",
    # Pre-defined pipelines
    "VERBOSITY_CONCISE_PIPELINE",
    "VERBOSITY_COT_PIPELINE",
    "HYBRID_COT_PIPELINE",
    "CONTEXT_SHORT_PIPELINE",
    "CONTEXT_LONG_PIPELINE",
    "REACT_RESEARCH_PIPELINE",
    "REACT_HYBRID_PIPELINE",
    "MULTITURN_SHORT_PIPELINE",
    "MULTITURN_LONG_PIPELINE",
    "SELF_CORRECTING_PIPELINE",
    "SELF_CORRECTING_HYBRID_PIPELINE",
    "RAG_BASIC_PIPELINE",
    "RAG_VERIFIED_PIPELINE",
    "RAG_HYBRID_PIPELINE",
    "DOC_ANALYSIS_SIMPLE_PIPELINE",
    "DOC_ANALYSIS_THOROUGH_PIPELINE",
    "DOC_ANALYSIS_ITERATIVE_PIPELINE",
    "DOC_ANALYSIS_HYBRID_PIPELINE",
]
