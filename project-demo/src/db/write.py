"""
Thread-safe database write operations.
"""

from typing import Optional
import json

from .connection import get_connection, get_lock


def log_run(
    workflow: str,
    pipeline: str,
    model: str,
    num_stages: int,
    total_input_tokens: int,
    total_output_tokens: int,
    total_cost: float,
    total_latency_ms: int,
    final_output: str = "",
    success: bool = True,
    error_message: Optional[str] = None,
    # Agentic metadata
    pipeline_type: str = "linear",
    iterations: int = 1,
    turns: int = 1,
    termination_reason: Optional[str] = None,
    avg_ttft_ms: Optional[float] = None,
    context_tokens_by_turn: Optional[str] = None,
    # A/B testing
    prompt_variant: Optional[str] = None,
    ab_test_name: Optional[str] = None,
) -> int:
    """Log a pipeline run to the database (thread-safe)."""
    with get_lock():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO runs (
                workflow, pipeline, pipeline_type, model, num_stages,
                total_input_tokens, total_output_tokens,
                total_cost, total_latency_ms, final_output,
                success, error_message,
                iterations, turns, termination_reason,
                avg_ttft_ms, context_tokens_by_turn,
                prompt_variant, ab_test_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow, pipeline, pipeline_type, model, num_stages,
            total_input_tokens, total_output_tokens,
            total_cost, total_latency_ms, final_output[:2000] if final_output else "",
            success, error_message,
            iterations, turns, termination_reason,
            avg_ttft_ms, context_tokens_by_turn,
            prompt_variant, ab_test_name
        ))
        
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return run_id


def log_stage(
    run_id: int,
    stage_order: int,
    stage_name: str,
    stage_type: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    latency_ms: int,
    success: bool = True,
    error_message: Optional[str] = None,
    iteration: Optional[int] = None,
    turn: Optional[int] = None,
    time_to_first_token_ms: Optional[int] = None,
    tokens_per_second: Optional[float] = None,
    prompt_variant: Optional[str] = None,
) -> int:
    """Log a pipeline stage result (thread-safe)."""
    with get_lock():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stages (
                run_id, stage_order, stage_name, stage_type, model,
                input_tokens, output_tokens, cost, latency_ms,
                success, error_message,
                iteration, turn,
                time_to_first_token_ms, tokens_per_second,
                prompt_variant
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, stage_order, stage_name, stage_type, model,
            input_tokens, output_tokens, cost, latency_ms,
            success, error_message,
            iteration, turn,
            time_to_first_token_ms, tokens_per_second,
            prompt_variant
        ))
        
        stage_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return stage_id


def log_quality_score(
    run_id: int,
    response_length: int,
    word_count: int,
    sentence_count: int,
    avg_sentence_length: float,
    has_structure: bool,
    vocabulary_richness: float,
    automated_score: float,
    relevance_score: Optional[float] = None,
    completeness_score: Optional[float] = None,
    clarity_score: Optional[float] = None,
    llm_score: Optional[float] = None,
    combined_score: Optional[float] = None,
    evaluation_cost: float = 0,
) -> int:
    """Log quality evaluation results (thread-safe)."""
    with get_lock():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quality_scores (
                run_id, response_length, word_count, sentence_count,
                avg_sentence_length, has_structure, vocabulary_richness,
                relevance_score, completeness_score, clarity_score,
                automated_score, llm_score, combined_score, evaluation_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, response_length, word_count, sentence_count,
            avg_sentence_length, has_structure, vocabulary_richness,
            relevance_score, completeness_score, clarity_score,
            automated_score, llm_score, combined_score, evaluation_cost
        ))
        
        score_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return score_id


def log_ab_test(
    test_name: str,
    prompt_name: str,
    variants: list,
    iterations_per_variant: int,
    description: str = "",
) -> int:
    """Log an A/B test experiment (thread-safe)."""
    with get_lock():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ab_tests (
                test_name, prompt_name, variants, 
                iterations_per_variant, total_runs, description
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            test_name, prompt_name, json.dumps(variants),
            iterations_per_variant, len(variants) * iterations_per_variant,
            description
        ))
        
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return test_id


def update_ab_test_status(test_name: str, status: str):
    """Update the status of an A/B test."""
    with get_lock():
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE ab_tests SET status = ? WHERE test_name = ?",
            (status, test_name)
        )
        
        conn.commit()
        conn.close()
