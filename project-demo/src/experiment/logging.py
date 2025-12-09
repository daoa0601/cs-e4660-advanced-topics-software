"""
Pipeline result logging.

Contains:
- log_pipeline_result(): Log pipeline execution to database
"""

import json

from ..config import get_model_id
from ..pipeline import PipelineResult
from ..evaluator import evaluate_automated, evaluate_with_llm
from ..db import log_run, log_stage, log_quality_score


def log_pipeline_result(
    workflow: str,
    result: PipelineResult,
    model: str,
    query: str,
    pipeline_type: str = "linear",
    evaluate_quality: bool = True,
    use_llm_eval: bool = False,
) -> int:
    """Log a complete pipeline result to the database."""

    # Calculate average TTFT if available
    ttfts = [s.time_to_first_token_ms for s in result.stages if s.time_to_first_token_ms]
    avg_ttft = sum(ttfts) / len(ttfts) if ttfts else None

    # Serialize context tokens by turn
    context_tokens_json = json.dumps(result.context_tokens_by_turn) if result.context_tokens_by_turn else None

    # Log the main run
    run_id = log_run(
        workflow=workflow,
        pipeline=result.pipeline_name,
        pipeline_type=pipeline_type,
        model=get_model_id(model),
        num_stages=len(result.stages),
        total_input_tokens=result.total_input_tokens,
        total_output_tokens=result.total_output_tokens,
        total_cost=result.total_cost,
        total_latency_ms=result.total_latency_ms,
        final_output=result.final_output[:2000] if result.final_output else "",
        success=result.success,
        iterations=result.iterations,
        turns=result.turns,
        termination_reason=result.termination_reason.value if result.termination_reason else None,
        avg_ttft_ms=avg_ttft,
        context_tokens_by_turn=context_tokens_json,
    )

    # Log each stage
    for stage in result.stages:
        log_stage(
            run_id=run_id,
            stage_order=stage.stage_order,
            stage_name=stage.stage_name,
            stage_type=stage.stage_type.value,
            model=stage.model,
            input_tokens=stage.input_tokens,
            output_tokens=stage.output_tokens,
            cost=stage.cost,
            latency_ms=stage.latency_ms,
            success=stage.success,
            error_message=stage.error_message,
            iteration=stage.iteration,
            turn=stage.turn,
            time_to_first_token_ms=stage.time_to_first_token_ms,
            tokens_per_second=stage.tokens_per_second,
        )

    # Evaluate and log quality
    if evaluate_quality and result.success and result.final_output:
        if use_llm_eval:
            quality = evaluate_with_llm(result.final_output, query)
        else:
            quality = evaluate_automated(result.final_output)

        log_quality_score(
            run_id=run_id,
            response_length=quality.response_length,
            word_count=quality.word_count,
            sentence_count=quality.sentence_count,
            avg_sentence_length=quality.avg_sentence_length,
            has_structure=quality.has_structure,
            vocabulary_richness=quality.vocabulary_richness,
            automated_score=quality.automated_score,
            relevance_score=quality.relevance_score,
            completeness_score=quality.completeness_score,
            clarity_score=quality.clarity_score,
            llm_score=quality.llm_score,
            combined_score=quality.combined_score,
            evaluation_cost=quality.llm_evaluation_cost,
        )

    return run_id
