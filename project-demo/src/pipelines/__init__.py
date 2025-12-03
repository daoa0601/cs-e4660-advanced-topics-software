"""
Pipeline module - re-exports from legacy pipeline.py for compatibility.

For new pipeline development, use the base classes from pipelines.base.
"""

# Re-export from legacy module for compatibility
from ..pipeline import (
    StageType,
    LoopTermination,
    StageResult,
    PipelineResult,
    PipelineStage,
    Pipeline,
    ReActPipeline,
    MultiTurnPipeline,
    SelfCorrectingPipeline,
    PIPELINES,
    get_pipeline,
    list_pipelines,
)

# Export base classes for new development
from .base import PipelineConfig

__all__ = [
    # Types
    "StageType",
    "LoopTermination",
    "StageResult",
    "PipelineResult",
    "PipelineStage",
    "PipelineConfig",
    # Pipeline classes
    "Pipeline",
    "ReActPipeline",
    "MultiTurnPipeline",
    "SelfCorrectingPipeline",
    # Registry
    "PIPELINES",
    "get_pipeline",
    "list_pipelines",
]
