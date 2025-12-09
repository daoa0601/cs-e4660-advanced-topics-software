"""
Base pipeline classes and data structures.

Contains:
- StageType, LoopTermination enums
- StageResult, PipelineResult dataclasses
- PipelineStage, Pipeline classes
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from ..clients import call_model, ModelResponse, StreamingMetrics
from ..cost_calculator import calculate_cost
from ..config import get_model_id


class StageType(Enum):
    """Types of pipeline stages."""
    GENERATION = "generation"
    CRITIQUE = "critique"
    REFINEMENT = "refinement"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    EVALUATION = "evaluation"
    # Agentic types
    THINKING = "thinking"       # ReAct: reasoning step
    ACTION = "action"           # ReAct: tool/action decision
    OBSERVATION = "observation" # ReAct: process results
    VALIDATION = "validation"   # Self-correcting: check output
    CONVERSATION = "conversation"  # Multi-turn
    # RAG types
    QUERY_UNDERSTANDING = "query_understanding"  # Parse and classify query
    RETRIEVAL = "retrieval"                      # Document retrieval (simulated)
    CONTEXT_ASSEMBLY = "context_assembly"        # Build context with docs
    VERIFICATION = "verification"                # Citation verification


class LoopTermination(Enum):
    """Reasons for loop termination."""
    MAX_ITERATIONS = "max_iterations"
    CONFIDENCE_REACHED = "confidence_reached"
    VALIDATION_PASSED = "validation_passed"
    ERROR = "error"


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    stage_name: str
    stage_type: StageType
    stage_order: int
    input_text: str
    output_text: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: int
    model: str
    success: bool = True
    error_message: Optional[str] = None
    # Streaming metrics
    time_to_first_token_ms: Optional[int] = None
    tokens_per_second: Optional[float] = None
    # Loop metadata
    iteration: Optional[int] = None
    turn: Optional[int] = None


@dataclass
class PipelineResult:
    """Complete result from a pipeline execution."""
    pipeline_name: str
    stages: list[StageResult]
    final_output: str
    total_cost: float
    total_latency_ms: int
    total_input_tokens: int
    total_output_tokens: int
    success: bool = True
    # Loop metadata
    iterations: int = 1
    termination_reason: Optional[LoopTermination] = None
    # Multi-turn metadata
    turns: int = 1
    context_tokens_by_turn: list[int] = field(default_factory=list)

    @property
    def stage_costs(self) -> dict[str, float]:
        """Get cost breakdown by stage."""
        return {s.stage_name: s.cost for s in self.stages}

    @property
    def cost_by_stage_type(self) -> dict[str, float]:
        """Get cost breakdown by stage type."""
        costs = {}
        for s in self.stages:
            stage_type = s.stage_type.value
            costs[stage_type] = costs.get(stage_type, 0) + s.cost
        return costs

    @property
    def cost_by_model(self) -> dict[str, float]:
        """Get cost breakdown by model."""
        costs = {}
        for s in self.stages:
            costs[s.model] = costs.get(s.model, 0) + s.cost
        return costs

    @property
    def avg_ttft_ms(self) -> Optional[float]:
        """Average time to first token across stages."""
        ttfts = [s.time_to_first_token_ms for s in self.stages if s.time_to_first_token_ms]
        return sum(ttfts) / len(ttfts) if ttfts else None


@dataclass
class PipelineStage:
    """Definition of a pipeline stage."""
    name: str
    stage_type: StageType
    prompt_template: str
    model_override: Optional[str] = None

    def build_prompt(self, **kwargs) -> str:
        """Build the prompt from template and variables."""
        return self.prompt_template.format(**kwargs)


@dataclass
class Pipeline:
    """A multi-stage LLM pipeline."""
    name: str
    description: str
    stages: list[PipelineStage]

    def execute(
        self,
        initial_input: str,
        model: str,
        context: Optional[dict] = None,
        streaming: bool = False,
    ) -> PipelineResult:
        """Execute the pipeline with the given input."""
        context = context or {}
        stage_results = []
        current_input = initial_input

        total_cost = 0
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0

        for i, stage in enumerate(self.stages):
            stage_model = stage.model_override or model

            prompt = stage.build_prompt(
                input=current_input,
                initial_input=initial_input,
                **context
            )

            response = call_model(prompt, stage_model, streaming=streaming)

            stage_cost = calculate_cost(
                response.input_tokens,
                response.output_tokens,
                stage_model
            )

            stage_result = StageResult(
                stage_name=stage.name,
                stage_type=stage.stage_type,
                stage_order=i + 1,
                input_text=prompt,
                output_text=response.text,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost=stage_cost,
                latency_ms=response.latency_ms,
                model=get_model_id(stage_model),
                success=response.success,
                error_message=response.error_message,
                time_to_first_token_ms=response.streaming_metrics.time_to_first_token_ms if response.streaming_metrics else None,
                tokens_per_second=response.streaming_metrics.tokens_per_second if response.streaming_metrics else None,
            )
            stage_results.append(stage_result)

            total_cost += stage_cost
            total_latency += response.latency_ms
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens

            if response.success:
                current_input = response.text
            else:
                return PipelineResult(
                    pipeline_name=self.name,
                    stages=stage_results,
                    final_output="",
                    total_cost=total_cost,
                    total_latency_ms=total_latency,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    success=False,
                )

        return PipelineResult(
            pipeline_name=self.name,
            stages=stage_results,
            final_output=current_input,
            total_cost=total_cost,
            total_latency_ms=total_latency,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            success=True,
        )
