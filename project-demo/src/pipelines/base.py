"""
Base classes and types for pipeline orchestration.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Callable, Any
from enum import Enum


class StageType(Enum):
    """Types of pipeline stages."""
    GENERATION = "generation"
    CRITIQUE = "critique"
    REFINEMENT = "refinement"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    EVALUATION = "evaluation"
    THINKING = "thinking"
    ACTION = "action"
    VALIDATION = "validation"
    CONVERSATION = "conversation"
    ANALYSIS = "analysis"
    CLASSIFICATION = "classification"
    RECOMMENDATION = "recommendation"


class LoopTermination(Enum):
    """Reasons for loop termination in agentic pipelines."""
    MAX_ITERATIONS = "max_iterations"
    CONFIDENCE_REACHED = "confidence_reached"
    VALIDATION_PASSED = "validation_passed"
    ERROR = "error"


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    stage_order: int
    stage_name: str
    stage_type: StageType
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: int
    output: str
    success: bool = True
    error_message: Optional[str] = None
    # Loop/turn tracking
    iteration: Optional[int] = None
    turn: Optional[int] = None
    # Streaming metrics
    time_to_first_token_ms: Optional[int] = None
    tokens_per_second: Optional[float] = None
    # A/B testing
    prompt_variant: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete result from a pipeline execution."""
    pipeline_name: str
    stages: List[StageResult]
    final_output: str
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    total_latency_ms: int
    success: bool = True
    # Agentic metadata
    iterations: int = 1
    turns: int = 1
    termination_reason: Optional[LoopTermination] = None
    context_tokens_by_turn: Optional[List[int]] = None
    # A/B testing
    prompt_variant: Optional[str] = None


@dataclass
class PipelineStage:
    """
    Definition of a pipeline stage.
    
    A stage transforms input to output, optionally using a specific model
    and prompt template.
    """
    name: str
    stage_type: StageType
    prompt_template: str
    model_override: Optional[str] = None  # If None, uses pipeline's default model
    prompt_variant: Optional[str] = None  # For A/B testing
    
    def build_prompt(self, input: str, **context) -> str:
        """Build the prompt for this stage."""
        return self.prompt_template.format(input=input, **context)


@dataclass 
class PipelineConfig:
    """Configuration for a pipeline."""
    name: str
    description: str = ""
    stages: List[PipelineStage] = field(default_factory=list)
    # A/B testing
    default_prompt_variant: Optional[str] = None
    
    def add_stage(self, stage: PipelineStage) -> 'PipelineConfig':
        """Add a stage to the pipeline (fluent interface)."""
        self.stages.append(stage)
        return self
